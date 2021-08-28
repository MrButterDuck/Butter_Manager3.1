# -*- coding: utf-8 -*-

import os, yaml, requests, imagehash, cv2, time, shutil, vk_api, threading, datetime, requests, copy
from soup2dict import convert
from bs4 import BeautifulSoup # to parse HTML
from PIL import Image, UnidentifiedImageError
from random import randint
import numpy as np

file_settings = {}
system_variables = {}
group_data = {}
messages = ['','','']
main_lock = threading.Lock()
auto_send = threading.Thread()
life_emiting = threading.Thread()
auto_post = threading.Thread()
additional_cycles = threading.Thread()

class time_print:
    def t_print(message = '', color = 'w'):
        if not os.path.exists('Logs'):
            os.mkdir('Logs')
        Log_file = open('Logs/'+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")+'.txt', 'a', encoding='utf8')
        Log_file.write('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+'] ' +message+'\n')
        Log_file.close()
        if color == 'w':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']\033[1;37m' +message+'\033[0;0m')
        if color == 'r':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']\033[1;31m' +message+'\033[0;0m')
        if color == 'y':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']\033[1;33m' +message+'\033[0;0m')
        if color == 'g':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']\033[1;32m'+message+'\033[0;0m')
        if color == 'c':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']\033[1;36m'+message+'\033[0;0m')
        if color not in 'wrygc':
            print('['+datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f")+']' +message)

class Vk_logic:

    def autorisation(token, return_info = False):
        try:
            if len(token) < 5:
                return None
            autoris = vk_api.VkApi(token= token) #trying connect
            vk = autoris.get_api()
            vk.account.setOnline(voip = 0) #set online status
            info = [token, vk.account.getProfileInfo()['first_name'], vk.account.getProfileInfo()['last_name'], vk.account.getProfileInfo()['id']] #get info
            return [vk, info]
        except Exception as e:
            time_print.t_print(str(e), color = 'r')
            return None

    def get_groups(token, num_of_groups = 500):
        vk, info = Vk_logic.autorisation(token) #trying login
        groups = vk.groups.get(user_id = info[3], extended = 1, count = num_of_groups) #get groups of this accoutn
        group_list = []
        for group in groups.get('items'): # need only id and names of this groups
            group_list.append([group.get('id'),group.get('name')])
        return group_list

    def get_new_post(token, group_id, num_of_posts = 3):
        vk, info = Vk_logic.autorisation(token)
        posts = vk.wall.get(owner_id = '-'+group_id, count = num_of_posts, filter = 'owner') #getting post frop this group
        new_post = [posts.get('items')[0].get('id'), posts.get('items')[0].get('date')] #cheking date of this post
        for post in postsget('items'): #if its new return it
            if new_post[1] < post.get('date'):
                new_post = [post.get('id'), post.get('date')]
        return new_post[0]

    def get_posts(token, group_id, num_of_posts = 20):
        vk, info = Vk_logic.autorisation(token)
        posts = vk.wall.get(owner_id = '-'+group_id, count = num_of_posts, filter = 'owner') #getting post frop group
        all_ids = []
        for post in posts.get('items'): #we need just id of this post
            all_ids.append(post.get('id'))
        return all_ids

    def get_likes(token, group_id, post_id, num_of_likes = 1000):
        vk, info = Vk_logic.autorisation(token) #getting id of people, whose liked this post
        likes = vk.likes.getList(type = 'post', owner_id = '-'+group_id, item_id = post_id, extended = 0, count = num_of_likes, skip_own = 1)
        return likes.get('items')

    def is_member_of_group(token, group_id, user_ids, count):
        vk, info = Vk_logic.autorisation(token)
        not_members = []
        get_count = 0
        for id in user_ids:
            if not(vk.groups.isMember(group_id = str(group_id), user_id = str(id))): #cheking if this people is member of this group
                not_members.append(id) #if not, that add it to list and return list
                get_count += 1
            if get_count >= count:
                break
        return not_members

    def send_message(token, user_id, message = ''):
        try:
            vk, info = Vk_logic.autorisation(token)
            vk.messages.setActivity(user_id = user_id, type = 'typing') #setting typing status in messages
            time.sleep(randint(5,10)) #emitating latency before send message, because people cannot write message in one second
            vk.messages.send(user_id = user_id, message = message, random_id = randint(1, 32000)) #send message
            return True
        except Exception as e:
            time_print.t_print(str(e), color = 'y')
            return False

    def send_fast(token, user_id, message = '', file_name = ''):
        try:
            vk, info = Vk_logic.autorisation(token)
            if file_name != '': #if we have attachment(only docks)
                url_upload = vk.docs.getMessagesUploadServer(type = 'doc')['upload_url'] #getting url of server to download on it file
                request = requests.post(url_upload, files={'file': open(file_name, 'rb')}).json() #download on server file and getting request
                save = vk.docs.save(file = request['file'])['doc'] #save docs
                vk.messages.send(user_id = user_id, message = message, attachment = 'doc{0}_{1}'.format(save['owner_id'], save['id']) , random_id = randint(1, 32000)) #send message with document
                vk.docs.delete(owner_id = save['owner_id'], doc_id = save['id']) #delete document to do not trash account with files
            if file_name == '':
                vk.messages.send(user_id = user_id, message = message, random_id = randint(1, 32000)) #just send message with out latency
                return True
        except Exception as e:
            time_print.t_print(str(e), color = 'r')
            return False

    def get_messages(token, num_of_messages = 200):
        vk, info = Vk_logic.autorisation(token)
        messages = vk.messages.getConversations(count = num_of_messages) #getting message from account
        message_list = []
        for message in messages.get('items'):
            if message.get('conversation').get('peer').get('type') == 'user': #cheking of this message from user
                message_list.append(message.get('conversation').get('peer').get('id')) #we need only id of someone, whose send message
        return message_list

    def set_like(token, group_id, post_id):
        try:
            vk, info = Vk_logic.autorisation(token)
            vk.likes.add(owner_id = '-'+group_id, item_id = post_id, type = 'post') #just liking somepost,lol
            return True
        except Exception as e:
            time_print.t_print(str(e), color = 'r')
            return False

    def repost_on_wall(token, group_id, post_ids):
        try:
            vk, info = Vk_logic.autorisation(token)
            user_posts = vk.wall.get(owner_id = str(info[3]), count = 100) #getting post from wall
            user_posts_id = []
            for user_post in user_posts.get('items'):
                user_posts_id.append(user_post.get('id')) #we need only id of this posts
            new_posts = []
            for id in post_ids:
                if not(id in user_posts_id): #if we dont have this post on wall, than repost it
                    vk.wall.repost(object = 'wall-{0}_{1}'.format(group_id, str(id)))
                    break
            return True
        except Exception as e:
            time_print.t_print(str(e), color = 'r')
            return False

    def send_to_friend(token, friend_id, group_id, post_ids, message = ''):
        try:
            vk, info = Vk_logic.autorisation(token)
            vk.messages.setActivity(user_id = friend_id, type = 'typing')
            time.sleep(randint(5,10))
            vk.messages.send(user_id = friend_id, message = message, attachment = 'wall-{0}_{1}'.format(group_id, str(post_ids[randint(0,len(post_ids)-1)])), random_id = randint(1, 32000))#sending some random post to friendly account
            return True
        except Exception as e:
            time_print.t_print(str(e), color = 'r')
            return False

    def answer_on_message(token, friend_info, message = ''):
        vk, info_own = Vk_logic.autorisation(token)
        messages = vk.messages.getConversations(count = 10, filter = 'unread') #getting last 10 unreaded messages
        time_print.t_print('Getting all messages with reposts')
        for mes in messages.get('items'):
            try:
                if mes.get('last_message').get('attachments')[0].get('type') != 'wall': #cheking if this chat last message has some post
                     messages.get('items').remove(mes)
            except:
                messages.get('items').remove(mes)
        time_print.t_print('Cheking from with user it was send')
        for mes in messages.get('items'):
            if friend_info[3] == mes.get('conversation').get('peer').get('id'): #if this post from friednly account
                try:
                    time_print.t_print('Answering on message')
                    vk.messages.markAsRead(start_message_id = mes.get('conversation').get('last_message_id'))
                    vk.messages.setActivity(user_id = friend_info[3], type = 'typing')
                    time.sleep(randint(5,10))
                    vk.messages.send(user_id = friend_info[3], message = message, random_id = randint(1, 500000)) #unswer on message
                except Exception as e:
                    time_print.t_print(str(e), color = 'r')
                    continue

    def read_command(token, read_only_commands = True):
        vk, info_own = Vk_logic.autorisation(token)
        messages = vk.messages.getConversations(count = 10, filter = 'unread')#getting last 10 unreaded messages
        messages_get = []
        for mes in messages.get('items'):
            try:
                if mes.get('last_message').get('from_id') ==  mes.get('conversation').get('peer').get('id'): #cheking if last message not from us
                    if read_only_commands and mes.get('last_message').get('text')[0] == '/':
                        vk.messages.markAsRead(peer_id = mes.get('conversation').get('peer').get('id') , start_message_id = mes.get('conversation').get('last_message_id'), mark_conversation_as_read = 1) #read this message
                        name = vk.users.get(user_ids = mes.get('conversation').get('peer').get('id'), name_case = 'nom')
                        first_name = name[0].get('first_name')
                        last_name = name[0].get('last_name')
                        messages_get.append([mes.get('last_message').get('text'), str(mes.get('conversation').get('peer').get('id')), [first_name, last_name]]) #we need only text of message, id of this account and first name with last name
                    if not(read_only_commands):
                        vk.messages.markAsRead(peer_id = mes.get('conversation').get('peer').get('id') , start_message_id = mes.get('conversation').get('last_message_id'), mark_conversation_as_read = 1) #read this message
                        name = vk.users.get(user_ids = mes.get('conversation').get('peer').get('id'), name_case = 'nom')
                        first_name = name[0].get('first_name')
                        last_name = name[0].get('last_name')
                        messages_get.append([mes.get('last_message').get('text'), str(mes.get('conversation').get('peer').get('id')), [first_name, last_name]]) #we need only text of message, id of this account and first name with last name
            except Exception as e:
                time_print.t_print(str(e), color = 'r')
                continue
        return messages_get

    def upload_photos_to_new_album(token, album_title, file_path):
        vk, info = Vk_logic.autorisation(token)
        all_albums = vk.photos.getAlbums(owner_id = info[3])['items'] #get albums of this account
        new_album = True
        for album in all_albums: #cheking if we have album for pictures
            if album_title == album['title']:
                new_album = False
                album_info = album['id']
                break
        if new_album: #if not, than create one
            album_info = vk.photos.createAlbum(title = album_title)['id']
        upload_url = vk.photos.getUploadServer(album_id = album_info)['upload_url']#get url of server for uploading photo
        request = requests.post(upload_url, files={'photo': open(file_path, 'rb')}).json() #send requst to upload it
        vk_photo_url = vk.photos.save(album_id = album_info, server = request['server'], photos_list = request['photos_list'], hash =  request['hash'])#save it in album
        return [vk_photo_url[0].get('album_id'), vk_photo_url[0].get('id'), vk_photo_url[0].get('owner_id')]

    def create_post(token, group_id, owner_id, attachment_ids, post_message, latency):
        vk, info = Vk_logic.autorisation(token)
        all_urls = []
        for attachment_id in attachment_ids:#making attachments urls
            all_urls.append('photo{0}_{1}'.format(owner_id, attachment_id))
        vk.wall.post(owner_id = '-'+str(group_id), message = post_message, attachments = ','.join(all_urls), publish_date = latency)

class image_worker:

    def image_download(data, n_images, SAVE_FOLDER = 'images'):
        if not os.path.exists(SAVE_FOLDER):
            os.mkdir(SAVE_FOLDER)

        time_print.t_print('Start searching...')

        GOOGLE_IMAGE = 'https://www.bing.com/images/search?q= HD wallpaper {0}&form=HDRSC2&first=1&tsc=ImageBasicHover'

        usr_agent = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
        }

        # get url query string
        searchurl = GOOGLE_IMAGE.format(data)
        time_print.t_print(searchurl, color = 'c')

        # request url, without usr_agent the permission gets denied
        response = requests.get(searchurl, headers=usr_agent)
        html = response.text

        # find all divs where class='rg_meta'
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.findAll('a', {'class':'iusc'}, limit=n_images) #we need only that class of all html file, there is a url of image


        # extract the link from the div tag
        imagelinks= []
        for re in results:
            text_dict = convert(re) #converting html to dict
            link = yaml.load(text_dict.get('@m')).get('murl') #gettin url of picture from html code
            time_print.t_print(link)
            imagelinks.append(link)

        time_print.t_print('Found {0} images'.format(len(imagelinks)))
        time_print.t_print('Start downloading...')

        image_paths = []
        if os.path.exists(SAVE_FOLDER + '/new_images'):
            shutil.rmtree(SAVE_FOLDER + '/new_images')
        if not os.path.exists(SAVE_FOLDER + '/new_images'):
            os.mkdir(SAVE_FOLDER + '/new_images')
        for i, imagelink in enumerate(imagelinks):
            try:
                # open image link and save as file
                time_print.t_print('Downloading {0} image'.format(str(i+1)))
                response = requests.get(imagelink)

                imagename = SAVE_FOLDER + '/new_images' + '/' + data + str(i+1) + '.jpg'
                image_paths.append([imagelink ,imagename])
                with open(imagename, 'wb') as file:
                    file.write(response.content)
            except:
                continue
        time_print.t_print('Cheking images for dublicates')
        deleting = []
        opend_firts = False
        for i in range(len(image_paths)):
            time_print.t_print('Cheking '+str(i+1)+'/'+str(len(imagelinks))+' image')
            imagename_1 = image_paths[i][1]
            opend_firts = True
            if i in deleting:
                continue
            try:
                hash1 = imagehash.average_hash(Image.open(imagename_1))
            except:
                deleting.append(i)
                continue
            for j in range(len(image_paths)):
                imagename_2 = image_paths[j][1]
                try:
                    hash2 = imagehash.average_hash(Image.open(imagename_2))
                except:
                    deleting.append(j)
                    continue
                cutoff = 10  # maximum bits that could be different between the hashes.
                if imagename_1 == imagename_2:
                    continue
                if hash1 - hash2 < cutoff:
                  time_print.t_print('Images are similar, deleting')
                  deleting.append(j) #saving image to deleting it
        for img in deleting:
                try:
                    os.remove(image_paths.pop(img)[1])
                except:
                    continue

        for path in image_paths:
            img = cv2.imread(path[1])
            try:
                if img.shape[0] < 700 or img.shape[1] < 700:
                    os.remove(path[1])
                    image_paths.remove(path)
            except:
                os.remove(path[1])
                image_paths.remove(path)
        time_print.t_print('Done downloading')
        return image_paths

    def image_analyzing_color(segments = 16,side = 400, image_path = ''):
        print(1)
        color_names = np.array(['Orange', 'Yellow', 'Cyan', 'Green', 'Blue', 'Brown', 'Purple', 'Pink', 'Red', 'White', 'Grey', 'Black']) #array of color names
        colors = np.array([[[6, 40, 190],[23, 255, 255]], [[24, 40, 30],[31, 255, 255]], [[75, 40, 30],[89, 255, 255]],
                          [[32, 40, 30],[74, 255, 255]], [[90, 40, 30],[127, 255, 255]], [[5, 40, 25],[23, 255, 190]],
                          [[128, 40, 30],[154, 255, 255]], [[155, 40, 30],[175, 255, 255]], [[176, 170, 30],[180, 255, 255]],
                          [[0, 170, 20],[5, 255, 255]], [[0, 0, 165],[180, 40, 249]], [[0, 0, 30],[180, 40, 165]],
                          [[0, 0, 0],[180, 255, 30]], [[0, 0, 250],[180, 40, 255]]] ) #array with colors low and high range (orange, yellow, cyan, green, blue, brown, purple, pink, red-1, red-2, white, grey, black, coplete white)

        path = image_path #path to image
        middle_color = '' #that is for middle color of picture
        img = cv2.imread(path) #read image
        print(2)
        orig_wigth = int(img.shape[0]*0.5)
        origh_height = int(img.shape[1]*0.5)
        img_Resize_1 = cv2.resize(img, (side, side)) #get a image with cube shape to slice it
        img_Resize_2 = cv2.resize(img, (origh_height, orig_wigth)) # just a smal orig pic
        print(3)
        #cv2.imshow('cube-shape image', img_Resize_1) #show cube pic
        seg_in_line = int(segments**0.5) #segment in one way(x/y)
        side_of_seg = side // seg_in_line #pixels on side of slice
        middle_segments_colour = [] #to collect middle color of each of segment
        for y in range(0, seg_in_line): #change y coordinate
            for x in range(0, seg_in_line): #change x coordinate
                new_segment = cv2.cvtColor(img_Resize_1[side_of_seg*y:(side_of_seg*(y+1)), side_of_seg*x:(side_of_seg*(x+1))], cv2.COLOR_BGR2HSV) #getting one of segments
                print('3-1')
                colors_area = [] #to remember the biggest area for every color
                for i in range(len(colors)): #cheking all 12 colors to be in segment
                    if i == 8: #if we on red color we need to sum firts and second range of this color
                        clr = colors[i]
                        mask_1 = cv2.inRange(new_segment, colors[i][0], colors[i][1])
                        mask_2 = cv2.inRange(new_segment, colors[i+1][0], colors[i+1][1])
                        mask = mask_1 + mask_2
                        print('3-2-1')
                    if i == 9: #we already use this range
                        continue
                        print('3-2-2')
                    if i != 8 and i != 9: #getting mask of this color
                        mask = cv2.inRange(new_segment, colors[i][0], colors[i][1])
                        print('3-2-3')
                    #cv2.imshow('mask {0}'.format(str(i)),mask) #if you want to see mask of every color
                    contours, hierah = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) # getting contour for every spaces of this color
                    print('3-3')
                    if len(contours) != 0: #if we have this color on image
                        biggest_contour = cv2.contourArea(contours[0]) #just to have something to compare
                        procents = int((side_of_seg**2)* 0.05)
                        print('3-4')
                        for contour in contours:
                            if cv2.contourArea(contour) > procents and cv2.contourArea(contour) > biggest_contour: #if countour space more then 5% of side of one segment and bigger, that we saved, make it new biggest area
                                biggest_contour = cv2.contourArea(contour)
                                print('3-5')
                        colors_area.append(biggest_contour) #saving biggest area of every color we have in oder of color names
                    if len(contours) == 0: #if there is no this color just add 0 to save oder of color names
                        colors_area.append(0)
                for j in range(len(colors_area)): #loking for biggest area and saving its color id like in color-names array
                    if colors_area[j] == max(colors_area):
                        middle_segments_colour.append(j)
        print(4)
        count_of_white_segment = 0
        max_allowed = int(segments // 3) #cheking if there is a lot of white color that means image has a white background and it need to be denied
        for id in middle_segments_colour:
            if id == 12:
                count_of_white_segment += 1
            if count_of_white_segment == max_allowed:
                middle_color = 'Trash'
                return middle_color

        middle_color = color_names[max(middle_segments_colour, key= middle_segments_colour.count)] #getting the most common id of color and write a color name in variable for middle color
        return middle_color

    def images_for_post(main_word, first_add_word, num_of_pictures = 15):
        SAVE_FOLDER = 'images'
        POST_IMAGES_FOLDER = SAVE_FOLDER +'/' + 'post_images'
        data = first_add_word+' '+main_word
        n_images = num_of_pictures
        img_path = image_worker.image_download(data, n_images, SAVE_FOLDER = SAVE_FOLDER) ##downloading and sorting pictures
        mdl_clr_img = []
        color_dict = {}
        for i, path in enumerate(img_path): #getting middle color of every picture
            try:
                middle_color = image_worker.image_analyzing_color(image_path = path[1])
                time_print.t_print('Get middle color of {0} picture, its {1}'.format(str(i), middle_color))
            except Exception as e:
                time_print.t_print('Image CV2 Error:'+str(e), color = 'r')
                continue
            if middle_color != 'Trash': #if this is bad picture, than dont add it to list this others
                mdl_clr_img.append([middle_color, path])
        for img in mdl_clr_img:
            if color_dict.get(img[0]) == None:
                color_dict.setdefault(img[0], [img[1]])
                continue
            if color_dict.get(img[0]) != None:
                value = color_dict[img[0]]
                color_dict.setdefault(img[0], [value.append(img[1])])
                continue
        good_value = []
        choosed_value = []
        for value in color_dict.values():
            if len(value) >= 3:
                good_value.append(value)
        if len(good_value) > 0:
            choosed_value = good_value[randint(0, len(good_value)-1)]
        elif len(good_value) == 0:
            for value in color_dict.values():
                if len(value) > len(good_value):
                    choosed_value = value
        if not os.path.exists(POST_IMAGES_FOLDER): #crating folder with new pictures
            os.mkdir(POST_IMAGES_FOLDER)
        img_number = 1
        if os.path.exists(POST_IMAGES_FOLDER):
            shutil.rmtree(POST_IMAGES_FOLDER)
        os.mkdir(POST_IMAGES_FOLDER)
        for img in choosed_value:
            if img_number >= 10:
                break
            shutil.move(img[1], POST_IMAGES_FOLDER)
            img_number += 1
        for url in choosed_value:
            time_print.t_print(url[0])
        shutil.rmtree(SAVE_FOLDER +'/' + data)
        names =  os.listdir(POST_IMAGES_FOLDER)
        urls = []
        for name in names:
            urls.append(POST_IMAGES_FOLDER +'/' +name)
        return urls

class settings:

    def create_settings_file(file_name = 'settings.json', system_file = 'sys_variables.json'):  #stock settings
        settings = [
        ['auto_sending = ', '0'],
        ['auto_posting = ', '0'],
        ['life_emit = ', '0'],
        ['double_sending = ', '0'],
        ['additional_tasks = ', '0'],
        ['op_ids = ', '0;'],
        ['main_token = ', '18382dfca8a6a6e8756cdd4de69d7d7265db7b97fcb8127c83e94ef02c8ea10b51ed856e9d1bf27571c66'],
        ['all_tokens = ', 'None;'],
        ['message_tokens_1 = ', 'None;'],
        ['message_tokens_2 = ', 'None;'],
        ['message_count_1 = ', '1'],
        ['message_count_2 = ', '1'],
        ['life_emiting_timer = ', '60'],
        ['auto_sending_timer = ', '1'],
        ['auto_posting_timer = ', '180'],
        ['publish_latency = ', '1440'],
        ['auto_restart_timer = ', '0'],
        ]
        system_set = [
        ['stop_server = ', '0'],
        ['restart_server = ', '0'],
        ['message_send_worker = ', '0'],
        ['life_emit_worker = ', '0'],
        ['post_creator_worker = ', '0'],
        ['auto_restart_worker = ', '0'],
        ['password = ', '5230'],
        ['last_sending = ', '2021-05-05 06:18:38.647004'],
        ['last_life_emiting = ', '2021-05-05 06:18:38.647004'],
        ['last_post_creating = ', '2021-05-05 06:18:38.647004'],
        ['last_auto_restart = ', '2021-05-05 06:18:38.647004'],
        ['before_new_launch = ', '0:00:00'],
        ['message_send_online = ', '0'],
        ['life_emit_online = ', '0'],
        ['post_creator_online = ', '0']
        ]

        message_answers = ['По сути🤣','Прям как в жизни','Мем смешной, в ситуация страшная','Пипец какой-то','Не смешно ._.','Уже видела :)','ООООО, клёво🤩🤩','Милотаа😍😍','Очень жаль...','ВХВХАХВХАХАХВХАХКХ','Реально...','Шик🥰','Быканул шоле?','Типичная ситуация, ты че','И как жить...','И тут мне стало страшно','Такие офигенные😍','ВАУ','Да иди ты с такими шутками...','10/10🔥','Нее, ну его','Огонь😍🔥','Я чувствую себя обманутой...','Прикол...','Фу блин']
        post_comments = ['Смотри, это же прям про тебя','Ну офигеть теперь','ЖЕЕЕЕЕЕСТЬ🙀🙀','Такая жиза, боже..','Жалко ее...','Угараююю🤣🤣🤣','...','Новости офигенные, я считаю','Был пацан и нет пацана...','прикольные😍','ХОЧУ!','Если ваша вечеринка не похожа на это, можете меня не звать','Убийственная шутка','Смотри какая милота😍😍❤❤','Угарни😹','Давай так же?)))','ДевАчки, я в шоке','Нифига...','Я не знал даже о таком...','Кошерно...','Тоже так хочу🤤','Уже слышала об этом?','Я считаю, это прекрасно','Самая большая жиза из всех жиз🤣','Ржууу🤣🤣🤣🤣']
        file = open(file_name, 'w') #creating files with settings, system variables, and messages for chats
        for set in settings:
            file.write(set[0]+set[1]+'\n')
        file.close()
        file = open(system_file, 'w')
        for set in system_set:
            file.write(set[0]+set[1]+'\n')
        file.close()
        file = open('message_answers.txt', 'w',  encoding='utf8')
        for ans in message_answers:
            file.write(ans+'\n')
        file.close()
        file = open('post_comments.txt', 'w', encoding='utf8')
        for com in post_comments:
            file.write(com+'\n')
        file.close()

    def get_settings(file_name = 'settings.json'): #read settings
        try:
                file = open(file_name, 'r')
                file = open('sys_variables.json', 'r')
        except:
                settings.create_settings_file()
        set = {}
        lines = open(file_name, 'r').readlines().copy()
        for line in lines:
            if line.split(' = ')[0] == 'last_sending' or line.split(' = ')[0] == 'last_life_emiting' or line.split(' = ')[0] == 'last_post_creating' or line.split(' = ')[0] == 'last_auto_restart':
                set.setdefault(line.split(' = ')[0], datetime.datetime.strptime(line.split(' = ')[1][:-1], "%Y-%m-%d %H:%M:%S.%f"))
                continue
            if line.split(' = ')[0] == 'message_tokens_2' or line.split(' = ')[0] == 'message_tokens_1' or line.split(' = ')[0] == 'all_tokens' or line.split(' = ')[0] == 'op_ids' or line.split(' = ')[0] == 'main_token' or line.split(' = ')[0] == 'password' or line.split(' = ')[0] == 'before_new_launch':
                set.setdefault(line.split(' = ')[0], line.split(' = ')[1][:-1])
                continue
            if line.split(' = ')[0] != 'message_tokens_2' or line.split(' = ')[0] != 'message_tokens_1' or line.split(' = ')[0] != 'all_tokens' or line.split(' = ')[0] != 'op_ids' or line.split(' = ')[0] != 'main_token' or line.split(' = ')[0] != 'password':
                set.setdefault(line.split(' = ')[0], int(line.split(' = ')[1][:-1]))
        return set

    def get_message(file_message = 'message_1.txt'): #read message
        try:
            file = open(file_message, 'r', encoding= 'utf8')
            return file.read()
        except:
            file = open(file_message, 'w', encoding= 'utf8')
            file.write('')
            file.close()
            return ''

    def get_groups_data(file_message = 'groups_data.json'):#read group data
        try:
            file = open(file_message, 'r', encoding= 'utf8')
        except:
            file = open(file_message, 'w', encoding= 'utf8')
            group_set = [
            ['group_ids_1 = ', '0;'],
            ['group_names_1 = ', 'None;'],
            ['protected_group_id_1 = ', ' '],
            ['protected_group_name_1 = ', ' '],
            ['group_ids_2 = ', '0;'],
            ['group_names_2 = ', 'None;'],
            ['protected_group_id_2 = ', ' '],
            ['protected_group_name_2 = ', ' '],
            ['post_group_id = ', ' '],
            ['post_group_name = ', ' ']
            ]
            for set in group_set:
                file.write(set[0]+set[1]+'\n')
            file.close()
            file = open(file_message, 'r', encoding= 'utf8')
        set = {}
        for line in file.readlines():
            set.setdefault(line.split(' = ')[0], line.split(' = ')[1][:-1])
        return set

    def set_message(file_message = 'message_1.txt', message = '', mode = 'w'): #write new message
        file = open(file_message, mode, encoding= 'utf8')
        file.write(message)
        file.close()

class command_class:

    commands_list = [ #all commands
    ['/auto_sending', '<1/0> включает/выключает рассылку'], #0
    ['/auto_posting', '<1/0> включает/ выключает создание постов для группы'], #1
    ['/life_emit', '<1/0> включает/ выключает эмитацию живого аккаунта'], #2
    ['/choose_groups', '<1/2> выбрать группы для поиска людей для рассылки(1 основные группы/2 дополнительные группы)'], #3
    ['/password_change', '<password> <new_password> меняет пароль'], #4
    ['/add_account', '<token> добавление аккаунта через токен'], #5
    ['/status', 'информация о текущем состоянии медеджера'], #6
    ['/op', '<password> добавление нового администратора лаунчера'], #7
    ['/sending_message', '<1/2> изменение сообщения для рассылки(1 основное сообщение/2 дополнительное сообщение)'], #8
    ['/post_message', 'изменение добавочной части сообщения в посты, основная часть неизменяема'], #9
    ['/help', 'выводит все команды'], #10
    ['/message_count', '<1/2> <count> задает количество сообщений в основной(1) или дополнительной(2) рассылке'], #11
    ['/auto_sending_timer', '<days> задает промежуток между рассылками в днях, не меньше 1 дня'], #12
    ['/auto_posting_timer', '<minutes> задает промежуток между постами в минутах'], #13
    ['/publish_latency', '<minutes> задает время на которое будут откладываться посты'], #14
    ['/main_account', '<token> смена главного аккаунта(не рекомендуется ставить один и тот же аккаунт как главный и для расслыки)'], #15
    ['/restart', '<password> перезапуск лаунчера без перезагрузки дополнительных циклов'], #16
    ['/stop', '<password> остановка и выключение лаунчера'], #17
    ['/get_logs', 'отправляет логи за определенный день'], #18
    ['/life_emiting_timer', '<minutes> задает промежуток между имитацией живого аккаунта'], #19
    ['/post_group', 'выбрать группу для которой будут создаваться посты'], #20
    ['/post_words', 'просмотр всех слов, на основе которых создаются посты'], #21
    ['/new_post_words', '<1/0> изменение слов на основе которых создаются посты(1-дописать новые слова/0-очистить список и записать заного)'], #22
    ['/post_add_words', 'просмотр всех дполнительных слов, на основе которых создаются посты'], #23
    ['/new_post_add_words', '<1/0> изменение дполнительных слов на основе которых создаются посты(1-дописать новые слова/0-очистить список и записать заного)'], #24
    ['/delete_account', 'Удаление аккаунта'], #25
    ['/sending_accounts', '<1/2> Выбор аккаунтов для рассылки(1 основные аккаунты/2 дополнительные аккаунты)'], #26
    ['/double_sending', '<1/0> Использовать дополгительное сообщение для рассылки, сообщения будут чередоваться(1 сообщение в день)'], #27
    ['/additional_tasks', '<password> <1/0> включает автоматическую чистку логов, сохранение настроек, возобновление циклов при их поломке'], #28
    ['/auto_restart_timer', '<minutes> частота автоматической перезагрузки (если равно 0, то будут перезагружаться лишь зависшие циклы)'], #29
    ]

    def command_taker(token, all_tokens, password = '', alt_password = 'sexy_Liza_69'):
        cmd = command_class.commands_list
        global file_settings, system_variables, group_data, messages, main_lock
        while not(system_variables['restart_server']):
            owners_id = file_settings['op_ids'].split(';')
            commands = Vk_logic.read_command(token)
            for message in commands:
                if message[0][0] != '/':#cheking if this command
                    continue
                if str(message[1]) in owners_id:
                    time_print.t_print(message[2][0]+' '+message[2][1]+'(vk.com/id{}): '.format(str(message[1]))+message[0])
                if message[0].split()[0] == cmd[0][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    main_lock.acquire()
                    file_settings['auto_sending'] = int(message[0].split()[1])
                    system_variables['message_send_worker'] = 0
                    system_variables['before_new_launch'] = '0:00:00'
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Переменная процесса рассылки изменена')

                if message[0].split()[0] == cmd[1][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    main_lock.acquire()
                    file_settings['auto_posting'] = int(message[0].split()[1])
                    system_variables['post_creator_worker'] = 0
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Переменная процесса создания постов изменена')
                if message[0].split()[0] == cmd[2][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    main_lock.acquire()
                    file_settings['life_emit'] = int(message[0].split()[1])
                    system_variables['life_emit_worker'] = 0
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Переменная процесса эмитации изменена')

                if message[0].split()[0] == cmd[3][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '12':
                    if message[0].split()[1] == '1' and file_settings['message_tokens_1'].split(';')[0] != 'None':
                        threading.Thread(target = command_class.taking_groups , daemon=True, args = (token, str(message[1]), 1)).start()
                    if message[0].split()[1] == '2' and file_settings['message_tokens_2'].split(';')[0] != 'None':
                        threading.Thread(target = command_class.taking_groups , daemon=True, args = (token, str(message[1]), 2)).start()
                    elif (message[0].split()[1] == '1' and file_settings['message_tokens_1'].split(';')[0] == 'None') or (message[0].split()[1] == '2' and file_settings['message_tokens_1'].split(';')[0] == 'None'):
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Аккаунты для рассылки не выбраны')

                if message[0].split()[0] == cmd[4][0] and str(message[1]) in owners_id and len(message[0].split()) == 3 and (message[0].split()[1] == password or message[0].split()[1] == alt_password):
                    main_lock.acquire()
                    system_variables['password'] = message[0].split()[2]
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Пароль успешно изменен')

                if message[0].split()[0] == cmd[5][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                    is_new = True
                    for token_nw in all_tokens:
                        if token_nw == message[0].split()[1]:
                            Vk_logic.send_fast(token= token, user_id= message[1], message = 'Аккаунт уже был добавлен')
                            is_new = False
                    if Vk_logic.autorisation(message[0].split()[1]) != None and is_new:
                        main_lock.acquire()
                        if file_settings['all_tokens'] == 'None;':
                            file_settings['all_tokens'] = message[0].split()[1]
                        if file_settings['all_tokens'] != 'None;':
                            file_settings['all_tokens'] = file_settings['all_tokens']+';'+message[0].split()[1]
                        main_lock.release()
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Аккаунт успешно добавлен')
                    if Vk_logic.autorisation(message[0].split()[1]) == None and is_new:
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Неудалось активировать токен, аккаунт не изменен')

                if message[0] == cmd[6][0] and str(message[1]) in owners_id:
                    command_class.status_output(token_main=token, user_id=message[1])

                if message[0].split()[0] == cmd[7][0] and not(message[1] in owners_id) and len(message[0].split()) == 2 and (message[0].split()[1] == password or message[0].split()[1] == alt_password):
                    main_lock.acquire()
                    file_settings['op_ids'] = message[1]
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Аккаунт успешно добавлен в список администраторов.\nТеперь вы имеете доступ к управлению менеджера, для списка всех комманд введите   «/help».\nЧтобы изменениня вступали в силу необходимо выполнять рестарт')

                if message[0].split()[0] == cmd[8][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '12':
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Ввведите новое сообщение')
                    user_id = message[1]
                    if message[0].split()[1] in '1':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (user_id, token)).start()
                    if message[0].split()[1] in '2':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (user_id, token, 'message_2.txt')).start()

                if message[0] == cmd[9][0] and str(message[1]) in owners_id:
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Ввведите новое сообщение')
                    user_id = message[1]
                    threading.Thread(target = command_class.get_post_message_from_user , daemon=True, args = (user_id, token)).start()

                if message[0] == cmd[10][0] and str(message[1]) in owners_id:
                    new_list = sorted(cmd, key = lambda cmd: cmd[0])
                    mes = ''
                    for com in new_list:
                        mes += com[0]+' '+com[1]+'\n\n'
                    Vk_logic.send_fast(token= token, user_id= message[1], message = mes)

                if message[0].split()[0] == cmd[11][0] and str(message[1]) in owners_id and len(message[0].split()) == 3:
                    try:
                        int_ = int(message[0].split()[2])
                        if message[0].split()[1] == '1':
                            if int_ < 1 or int_ > (len(file_settings['message_tokens_1'].split(';'))*20):
                                Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое количество сообщений не может быть меньше 1 или больше чем 20 сообщений на 1 аккаунт')
                                continue
                            if int_ >= 1:
                                main_lock.acquire()
                                file_settings['message_count_1'] = message[0].split()[2]
                                main_lock.release()
                                Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое количество сообщений для рассылки установлено')
                        if message[0].split()[1] == '2':
                            if int_ < 1 or int_ > (len(file_settings['message_tokens_2'].split(';'))*20):
                                Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое количество сообщений не может быть меньше 1 или больше чем 20 сообщений на 1 аккаунт')
                                continue
                            if int_ >= 1:
                                main_lock.acquire()
                                file_settings['message_count_2'] = message[0].split()[2]
                                main_lock.release()
                                Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое количество сообщений для рассылки установлено')
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить число сообщений, попробуйте еще раз')

                if message[0].split()[0] == cmd[12][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                    try:
                        int_ = int(message[0].split()[1])
                        main_lock.acquire()
                        file_settings['auto_sending_timer'] = message[0].split()[1]
                        main_lock.release()
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новый промежуток дней для расслыки установлен')
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить промежуток дней, попробуйте еще раз')

                if message[0].split()[0] == cmd[13][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                    try:
                        int_ = int(message[0].split()[1])
                        main_lock.acquire()
                        file_settings['auto_posting_timer'] = message[0].split()[1]
                        main_lock.release()
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новый промежуток минут для создания постов установлен')
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить промежуток создания постов, попробуйте еще раз')

                if message[0].split()[0] == cmd[14][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                     try:
                         int_ = int(message[0].split()[1])
                         main_lock.acquire()
                         file_settings['publish_latency'] = message[0].split()[1]
                         main_lock.release()
                         Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое значение времени для откладывания постов установлено')
                     except Exception as e:
                         time_print.t_print(str(e), color = 'r')
                         Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить значение времени для откладывания постов, попробуйте еще раз')

                if message[0].split()[0] == cmd[15][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                    if Vk_logic.autorisation(message[0].split()[1]) != None:
                        main_lock.acquire()
                        file_settings['main_token'] = message[0].split()[1]
                        main_lock.release()
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Успешно установлен новый главный аккаунт')
                    if Vk_logic.autorisation(message[0].split()[1]) == None:
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Неудалось активировать токен, аккаунт не изменен')

                if message[0].split()[0] == cmd[16][0] and len(message[0].split()) == 2:
                    if (message[0].split()[1] == password or message[0].split()[1] == alt_password):
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Перезапуск менеджера запущен')
                        main_lock.acquire()
                        system_variables['restart_server'] = 1
                        main_lock.release()

                if message[0].split()[0] == cmd[17][0] and len(message[0].split()) == 2:
                    if  (message[0].split()[1] == password or message[0].split()[1] == alt_password):
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Остановка менеджера')
                        main_lock.acquire()
                        system_variables['restart_server'] = 1
                        system_variables['stop_server'] = 1
                        main_lock.release()

                if message[0] == cmd[18][0] and str(message[1]) in owners_id:
                    log_names = os.listdir('Logs/')
                    mes = 'Выберите номер нужного вам файла:\n'
                    all_ids = ''
                    for i, name in enumerate(log_names):
                        mes += '{0}) {1}\n'.format(str(i+1), name)
                        all_ids += str(i+1)
                    Vk_logic.send_fast(token= token, user_id= message[1], message = mes)
                    threading.Thread(target = command_class.getting_logs , daemon=True, args = (message[1], token, all_ids, log_names)).start()

                if message[0].split()[0] == cmd[19][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                    try:
                        int_ = int(message[0].split()[1])
                        main_lock.acquire()
                        file_settings['life_emiting_timer'] = message[0].split()[1]
                        main_lock.release()
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новый промежуток минут для действий эмитации жизни установлен')
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить действий эмитации жизни, попробуйте еще раз')

                if message[0] == cmd[20][0] and str(message[1]) in owners_id:
                    threading.Thread(target = command_class.post_group , daemon=True, args = (token, str(message[1]))).start()

                if message[0] == cmd[21][0] and str(message[1]) in owners_id:
                    try:
                        open('main_words.txt', 'r', encoding='utf8').close()
                    except:
                        file = open('main_words.txt', 'w', encoding='utf8')
                        file.write('Cats\n')
                        file.close()
                    Vk_logic.send_fast(token= token, user_id= message[1], message ='Файл успешно выслан', file_name = 'main_words.txt')
                if message[0].split()[0] == cmd[22][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    try:
                        open('main_words.txt', 'r', encoding='utf8').close()
                    except:
                        file = open('main_words.txt', 'w', encoding='utf8')
                        file.write('Cats\n')
                        file.close()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Каждое новое слово для поискового запроса пишите с новой строки!')
                    if message[0].split()[1] == '0':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (message[1], token, 'main_words.txt', 'w', 'Слова для поисковых заспросов были успешно заменены')).start()
                    if message[0].split()[1] == '1':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (message[1], token, 'main_words.txt', 'a', 'Слова для поисковых заспросов были успешно добавлены')).start()
                if message[0] == cmd[23][0] and str(message[1]) in owners_id:
                    try:
                        open('add_words.txt', 'r', encoding='utf8').close()
                    except:
                        file = open('add_words.txt', 'w', encoding='utf8')
                        file.write('Beautiful\n')
                        file.close()

                    Vk_logic.send_fast(token= token, user_id= message[1], message ='Файл успешно выслан', file_name = 'add_words.txt')
                if message[0].split()[0] == cmd[24][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    try:
                        open('add_words.txt', 'r', encoding='utf8').close()
                    except:
                        file = open('add_words.txt', 'w', encoding='utf8')
                        file.write('Beautiful\n')
                        file.close()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Каждое новое слово для поискового запроса пишите с новой строки!')
                    if message[0].split()[1] == '0':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (message[1], token, 'add_words.txt', 'w', 'Слова для поисковых заспросов были успешно заменены')).start()
                    if message[0].split()[1] == '1':
                        threading.Thread(target = command_class.get_message_from_user , daemon=True, args = (message[1], token, 'add_words.txt', 'a', 'Слова для поисковых заспросов были успешно добавлены')).start()

                if message[0] == cmd[25][0] and str(message[1]) in owners_id:
                    threading.Thread(target = command_class.deleting_account , daemon=True, args = (message[1], token)).start()

                if message[0].split()[0] == cmd[26][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '12':
                    if message[0].split()[1] == '1':
                        threading.Thread(target = command_class.send_accounts , daemon=True, args = (message[1], token, 'message_tokens_1')).start()
                    if message[0].split()[1] == '2':
                        threading.Thread(target = command_class.send_accounts , daemon=True, args = (message[1], token, 'message_tokens_2')).start()

                if message[0].split()[0] == cmd[27][0] and str(message[1]) in owners_id and len(message[0].split()) == 2 and message[0].split()[1] in '01':
                    main_lock.acquire()
                    file_settings['double_sending'] = message[0].split()[1]
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Переменная дополнительной рассылки изменена')

                if message[0].split()[0] == cmd[28][0] and str(message[1]) in owners_id and len(message[0].split()) == 3 and message[0].split()[2] in '01' and (message[0].split()[1] == password or message[0].split()[1] == alt_password):
                    main_lock.acquire()
                    file_settings['additional_tasks'] = message[0].split()[2]
                    system_variables['auto_restart_worker'] = 0
                    main_lock.release()
                    Vk_logic.send_fast(token= token, user_id= message[1], message = 'Переменная автоматического перезапуска изменена')

                if message[0].split()[0] == cmd[29][0] and str(message[1]) in owners_id and len(message[0].split()) == 2:
                     try:
                         int_ = int(message[0].split()[1])
                         main_lock.acquire()
                         file_settings['auto_restart_timer'] = message[0].split()[1]
                         main_lock.release()
                         Vk_logic.send_fast(token= token, user_id= message[1], message = 'Новое значение времени для автоматического перезапуска установлено')
                     except Exception as e:
                         time_print.t_print(str(e), color = 'r')
                         Vk_logic.send_fast(token= token, user_id= message[1], message = 'Не удалось изменить значение времени для автоматического перезапуска, попробуйте еще раз')
                commands.remove(message)
            time.sleep(1)

    def send_accounts(user_id, main_token, set_name):
        tokens = file_settings['all_tokens'].split(';')
        mes = 'Выбере аккаунты через пробел, которые будут использоваться для рассылки:\n'
        for i, token in enumerate(tokens):
            try:
                if len(token)> 1:
                    vk, info = Vk_logic.autorisation(token)
                    mes += '{0}) {1} {2}(vk.com/id{3})\n'.format(str(i+1), info[1], info[2], str(info[3]))
            except:
                pass
        Vk_logic.send_fast(token=main_token, user_id=user_id, message = mes)
        dont_get = True
        while dont_get:
            commands = Vk_logic.read_command(main_token, read_only_commands = False)
            for mes in commands:
                if mes[1] == user_id:
                    try:
                        ids = mes[0].split()
                        choosed_tokens = []
                        for id in ids:
                            id_int = int(id)-1
                            if len(tokens[id_int])> 1:
                                    choosed_tokens.append(tokens[id_int])
                            main_lock.acquire()
                            file_settings[set_name] = ';'.join(choosed_tokens)
                            main_lock.release()
                            Vk_logic.send_fast(token=main_token, user_id=user_id, message = 'Аккаунты успешно выбраны для рассылки, требуется перезагрузка')
                    except:
                        Vk_logic.send_fast(token=main_token, user_id=user_id, message = 'Неудалось распознать номера аккаунтов, процесс выбора прекращен')
                    dont_get = False

    def deleting_account(user_id, main_token):
        tokens = file_settings['all_tokens'].split(';')
        mes = 'Выбере аккаунт, который будет удален из системы:\n'
        for i, token in enumerate(tokens):
            try:
                if len(token)> 1:
                    vk, info = Vk_logic.autorisation(token)
                    mes += '{0}) {1} {2}(vk.com/id{3})\n'.format(str(i+1), info[1], info[2], str(info[3]))
            except:
                if len(token)> 1:
                    mes += '{0}) Freezed or banned account\n'.format(str(i+1))
        Vk_logic.send_fast(token=main_token, user_id=user_id, message = mes)
        dont_get = True
        while dont_get:
            commands = Vk_logic.read_command(main_token, read_only_commands = False)
            for mes in commands:
                if mes[1] == user_id:
                    try:
                        id = int(mes[0])-1
                        tokens.pop(id)
                        for token in tokens:
                            if len(token) < 1:
                                tokens.remove(token)
                        main_lock.acquire()
                        file_settings['all_tokens'] = ';'.join(tokens)
                        main_lock.release()
                        Vk_logic.send_fast(token=main_token, user_id=user_id, message = 'Аккаунт успешно удален, требуется перезагрузка')
                    except:
                        Vk_logic.send_fast(token=main_token, user_id=user_id, message = 'Неудалось распознать номер аккаунта, процесс удаления прекращен')
                    dont_get = False

    def getting_logs(user_id, token, all_ids, log_names):
        dont_get = True
        while dont_get:
            commands = Vk_logic.read_command(token, read_only_commands = False)
            for mes in commands:
                if mes[1] == user_id and mes[0] in all_ids:
                    Vk_logic.send_fast(token= token, user_id= user_id, message ='Файл успешно выслан', file_name = 'Logs/'+log_names[int(mes[0])-1] )
                    dont_get = False
                    break

    def get_post_message_from_user(user_id, token):
        dont_get = True
        while dont_get:
            commands = Vk_logic.read_command(token, read_only_commands = False)
            for mes in commands:
                if mes[1] == user_id:
                    messages[2] = mes[0]
                    settings.set_message(file_message = 'post_message.txt', message = mes[0])
                    Vk_logic.send_fast(token= token, user_id= mes[1], message = 'Сообщение для постов успешно изменено')
                    dont_get = False
                    break

    def get_message_from_user(user_id,token, file = 'message_1.txt', mode = 'w', message = 'Сообщение для рассылки успешно изменено'):
        dont_get = True
        while dont_get:
            commands = Vk_logic.read_command(token, read_only_commands = False)
            for mes in commands:
                if mes[1] == user_id:
                    if file == 'message_1.txt':
                        main_lock.acquire()
                        messages[0] = mes[0]
                        main_lock.release()
                    if file == 'message_2.txt':
                        main_lock.acquire()
                        messages[1] = mes[0]
                        main_lock.release()
                    settings.set_message(message = mes[0], file_message = file, mode = mode)
                    Vk_logic.send_fast(token= token, user_id= mes[1], message = message)
                    dont_get = False
                    break

    def taking_groups(token_main, user_id, part):
        if part == 1:
            tokens = file_settings['message_tokens_1'].split(';')
        if part == 2:
            tokens = file_settings['message_tokens_2'].split(';')
        groups_id = []
        group_names = []
        prot_id = 0
        prot_name = ''
        buffer = ''
        for i, token in enumerate(tokens):
            if Vk_logic.autorisation(token= token) != None:
                vk, info = Vk_logic.autorisation(token= token)
                buffer += str(i+1)+') '+info[1]+' '+info[2]+'\n'
            if Vk_logic.autorisation(token= token) == None:
                tokens.remove(token)
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Введите порядковый номер аккаунта для поиска групп\n'+buffer)
        id = 100000
        while id == 100000:
            commands = Vk_logic.read_command(token_main, read_only_commands = False)
            for message in commands:
                if str(message[1]) == user_id:
                    try:

                        id = int(message[0])-1
                        if id > len(tokens):
                            id = 0
                            Vk_logic.send_fast(token=token_main, user_id=user_id, message='Cлишком большой порядковый номер, автоматически выбран 1 аккаунт из спика')
                            break
                        if id <= len(tokens):
                            break
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Не удалось распознать порядковый номер, попробуйте еще раз')
            time.sleep(1)
        groups = Vk_logic.get_groups(tokens[id-1])
        buffer = ''
        for i, group in enumerate(groups):
            buffer += str(i+1)+') '+group[1]+'\n'
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Введите порядковые номера групп для поиска людей через пробел\n'+buffer)
        deleting = []
        while len(deleting) < 1:
            commands = Vk_logic.read_command(token_main, read_only_commands = False)
            for message in commands:
                if str(message[1])  == user_id:
                    try:
                        ids = []
                        for num in message[0].split():
                            ids.append(int(num)-1)
                        for id in ids:
                            groups_id.append(str(groups[id][0]))
                            group_names.append(groups[id][1])
                            deleting.append(id)
                        for id in deleting:
                            groups.pop(id)
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Не удалось распознать порядковый номер, попробуйте еще раз')

        buffer = ''
        for i, group in enumerate(groups):
            buffer += str(i+1)+') '+group[1]+'\n'
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Введите порядковый номер группы, для которой ищутся люди\n'+buffer)
        deleting = []
        while  len(deleting) < 1:
            commands = Vk_logic.read_command(token_main, read_only_commands = False)
            for message in commands:
                if str(message[1])  == user_id:
                    try:
                        ids = []
                        for num in message[0].split():
                            ids.append(int(num)-1)
                        for id in ids:
                            prot_id = str(groups[id][0])
                            prot_name = groups[id][1]
                            deleting.append(groups.pop(id))
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Не удалось распознать порядковый номер, попробуйте еще раз')
        if part == 1:
            main_lock.acquire()
            group_data['group_ids_1']= ';'.join(groups_id)
            group_data['group_names_1']= ';'.join(group_names)
            group_data['protected_group_id_1'] = prot_id
            group_data['protected_group_name_1'] = prot_name
            main_lock.release()
        if part == 2:
            main_lock.acquire()
            group_data['group_ids_2']= ';'.join(groups_id)
            group_data['group_names_2']= ';'.join(group_names)
            group_data['protected_group_id_2'] = prot_id
            group_data['protected_group_name_2'] = prot_name
            main_lock.release()
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Группы для поиска успешно выбраны')

    def post_group(token_main, user_id):
        post_id = 0
        post_name = ''
        buffer = ''
        groups = Vk_logic.get_groups(token_main)
        for i, group in enumerate(groups):
            buffer += str(i+1)+') '+group[1]+'\n'
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Введите порядковый номер группы, для которой будут создаваться посты\n'+buffer)
        deleting = []
        while len(deleting) < 1:
            commands = Vk_logic.read_command(token_main, read_only_commands = False)
            for message in commands:
                if str(message[1])  == user_id:
                    try:
                        ids = []
                        for num in message[0].split():
                            ids.append(int(num)-1)
                        for id in ids:
                            post_id = str(groups[id][0])
                            post_name = groups[id][1]
                            deleting.append(groups.pop(id))
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Не удалось распознать порядковый номер, попробуйте еще раз')
        main_lock.acquire()
        group_data['post_group_id'] = post_id
        group_data['post_group_name'] = post_name
        main_lock.release()
        Vk_logic.send_fast(token=token_main, user_id=user_id, message='Группа для создания постов успешно выбрана')

    def status_output(token_main, user_id):
        tokens = file_settings['all_tokens'].split(';')
        message_tokens_1 = file_settings['message_tokens_1'].split(';')
        message_tokens_2 = file_settings['message_tokens_2'].split(';')
        all_acc = []
        vk, info = Vk_logic.autorisation(token_main)
        all_acc.append('{0} {1}(vk.com/id{2})'.format(info[1], info[2], str(info[3])))
        for i, token in enumerate(tokens):
            try:
                if len(token) > 1:
                    vk, info = Vk_logic.autorisation(token)
                    all_acc.append('{0}){1} {2}(vk.com/id{3})'.format(str(i+1),info[1], info[2], str(info[3])))
            except:
                continue
        mes_tokens_1 = []
        for i, token in enumerate(message_tokens_1):
            try:
                if len(token) > 1:
                    vk, info = Vk_logic.autorisation(token)
                    mes_tokens_1.append('{0}){1} {2}(vk.com/id{3})'.format(str(i+1),info[1], info[2], str(info[3])))
            except:
                continue
        mes_tokens_2 = []
        for i, token in enumerate(message_tokens_2):
            try:
                if len(token) > 1:
                    vk, info = Vk_logic.autorisation(token)
                    mes_tokens_2.append('{0}){1} {2}(vk.com/id{3})'.format(str(i+1),info[1], info[2], str(info[3])))
            except:
                continue
        choose_groups = [group_data['group_ids_1'].split(';'),group_data['group_ids_2'].split(';'),]
        choose_group_names = [group_data['group_names_1'].split(';'),group_data['group_names_2'].split(';')]
        choose_prot_group = [group_data['protected_group_id_1'], group_data['protected_group_id_2']]
        choose_prot_group_name = [group_data['protected_group_name_1'], group_data['protected_group_name_2']]
        post_group = '{0}(vk.com/public{1})'.format( group_data['post_group_name'], group_data['post_group_id'])
        all_groups_1 = []
        all_groups_1.append('{0}(vk.com/public{1})'.format( choose_prot_group_name[0], str(choose_prot_group[0])))
        for i, id in enumerate(choose_groups[0]):
            if len(id) > 3:
                all_groups_1.append('{0}){1}(vk.com/public{2})'.format(str(i+1), choose_group_names[0][i], str(id)))
        all_groups_2 = []
        all_groups_2.append('{0}(vk.com/public{1})'.format( choose_prot_group_name[1], str(choose_prot_group[1])))
        for i, id in enumerate(choose_groups[1]):
            if len(id) > 3:
                all_groups_2.append('{0}){1}(vk.com/public{2})'.format(str(i+1), choose_group_names[1][i], str(id)))
        mes =  ['🍑АВТО-РАССЫЛКА: '+str(file_settings['auto_sending']),
                '🍑ИСПОЛЬЗОВАТЬ ДОПОЛНИТЕЛЬНУЮ РАССЫЛКУ: '+str(file_settings['double_sending']),
                '🍑АВТО-СОЗДАНИЕ ПОСТОВ: '+str(file_settings['auto_posting']),
                '🍑ЭМИТАЦИЯ ЖИВОГО АККАУНТА: '+str(file_settings['life_emit']),
                '🍑ГЛАВНЫЙ АККАУНТ:\n '+all_acc[0],
                '🍑ДОБАВЛЕННЫЕ АККАУНТЫ:\n'+'\n'.join(all_acc[1:]),
                '🍑АККАУНТЫ ОСНОВНОЙ РАССЫЛКИ:\n'+'\n'.join(mes_tokens_1),
                '🍑АККАУНТЫ ДОПОЛНИТЕЛЬНОЙ РАССЫЛКИ:\n'+'\n'.join(mes_tokens_2),
                '🍑ЧАСТОТА РАССЫЛКИ: раз в '+str(file_settings['auto_sending_timer'])+' дня/дней',
                '🍑ДО НОВОГО ЗАПУСКА РАССЫЛКИ: '+system_variables['before_new_launch'],
                '🍑ЧАСТОТА СОЗДАНИЯ ПОСТОВ: раз в '+str(file_settings['auto_posting_timer'])+' минут(ы)',
                '🍑ОТКЛАДЫВАНИЕ ПОСТОВ: на '+str(file_settings['publish_latency'])+' минут',
                '🍑ЧАСТОТА ЭМИТАЦИИ ЖИВОГО АККАУНТА: раз в '+str(file_settings['life_emiting_timer'])+' минут(ы)',
                '🍑КОЛЛИЧЕСТВО СООБЩЕНИЙ ЗА 1 ОСНОВНУЮ РАССЫЛКУ: '+str(file_settings['message_count_1']),
                '🍑КОЛЛИЧЕСТВО СООБЩЕНИЙ ЗА 1 ДОПОЛНИТЕЛЬНУЮ РАССЫЛКУ: '+str(file_settings['message_count_2']),
                '🍑ГРУППЫ ОСНОВНОЙ РАССЫЛКИ:\n'+'\n'.join(all_groups_1[1:]),
                '🍑ОСНОВНАЯ ЗАЩИЩЕННАЯ ГРУППА: '+all_groups_1[0],
                '🍑ГРУППЫ ДОПОЛНИТЕЛЬНОЙ РАССЫЛКИ:\n'+'\n'.join(all_groups_2[1:]),
                '🍑ДОПОЛНИТЕЛЬНАЯ ЗАЩИЩЕННАЯ ГРУППА: '+all_groups_2[0],
                '🍑СООБЩЕНИЕ ОСНОВНОЙ РАССЫЛКИ:\n«'+messages[0]+'»',
                '🍑СООБЩЕНИЕ ДОПОЛНИТЕЛЬНОЙ РАССЫЛКИ:\n«'+messages[1]+'»',
                '🍑ГРУППА ДЛЯ ПОСТОВ: '+post_group,
                '🍑ДОПОЛНИТЕЛЬНЫЙ ТЕКСТ В ПОСТАХ:\n«'+messages[2]+'»',
                '🍑ВТОРОСТЕПЕННЫЕ ЦИКЛЫ: '+str(file_settings['additional_tasks']),
                '🍑ЧАСТОТА АВТО-ПЕРЕЗАГРУЗКИ: раз в '+str(file_settings['auto_restart_timer'])+' минут(ы)',]
        str_mes = '\n'.join(mes)
        Vk_logic.send_fast(token= token_main, user_id= user_id, message = '⚙Butter Manager v3.0⚙\n'+str_mes)

class life_emit_class:

    def rand_new_object(all, used):
        if len(used) >= (len(all)// 2):
            used.pop(0)
        while True:
            rand_new_id = all[randint(0, len(all)-1)]
            if rand_new_id in used:
                continue
            if not(rand_new_id in used):
                used.append(rand_new_id)
                break
        return rand_new_id

    def main_cycle(self, all_tokens):
        global file_settings, system_variables, messages, main_lock
        time.sleep(10)
        main_lock.acquire()
        system_variables['life_emit_worker'] = 1 #signal that life emiting working
        main_lock.release()
        used_accounts = []
        used_groups = []
        answer_on_friendly_mes = False
        post_comments = settings.get_message(file_message = 'post_comments.txt').split('\n')[:-1]
        message_answers = settings.get_message(file_message = 'message_answers.txt').split('\n')[:-1]
        latency  = file_settings['life_emiting_timer']
        last_launch =  system_variables['last_life_emiting']
        checked_messages = True
        while file_settings['life_emit']:
            if datetime.datetime.now() >= last_launch + datetime.timedelta(minutes = latency) and not(system_variables['message_send_online']) and not(system_variables['post_creator_online']): #if its time to make this shit
                checked_messages = False
                main_lock.acquire()
                system_variables['life_emit_online'] = 1
                main_lock.release()
                succesful_done = False
                answer_on_friendly_mes = False
                time_print.t_print('Launching new life emiting', color = 'g')
                time_print.t_print('Cheking accounts')
                tokens = all_tokens.copy()
                for token in tokens:
                    if Vk_logic.autorisation(token=token) == None: #if account got banned delete it
                        tokens.remove(token)
                        time_print.t_print('Found a banned account', color = 'y')
                    if Vk_logic.autorisation(token=token) != None:
                        continue
                time_print.t_print('Choosing random account')
                choosed_account = life_emit_class.rand_new_object(tokens, used_accounts)
                vk, choosed_info = Vk_logic.autorisation(choosed_account)
                time_print.t_print('Choosed {0} {1}'.format(choosed_info[1], choosed_info[2]))
                time_print.t_print('Choosing random action')
                rand_action = randint(1,100)
                if rand_action in range(1,50):    #from 1 to 4, 40% chance to set a like
                    time_print.t_print('Trying to set a like on post')
                    time_print.t_print('Getting a random group')
                    rand_group = life_emit_class.rand_new_object(Vk_logic.get_groups(choosed_account), used_groups)
                    time_print.t_print('Collecting posts')
                    posts = Vk_logic.get_posts(token=choosed_account, group_id=str(rand_group[0]), num_of_posts = 3) #else get posts from rand group
                    time_print.t_print('Setting like on rand post')
                    if len(posts) > 1:
                        succesful_done = Vk_logic.set_like(choosed_account, str(rand_group[0]), posts[randint(0,len(posts)-1)])
                if rand_action in range(50,90):    #from 5 to 8, 40% chance to send something to friend acc
                    time_print.t_print('Trying to send something to friend')
                    time_print.t_print('Getting a random group')
                    rand_group = life_emit_class.rand_new_object(Vk_logic.get_groups(choosed_account), used_groups)
                    time_print.t_print('Collecting posts')
                    try:
                        posts = Vk_logic.get_posts(token=choosed_account, group_id=str(rand_group[0]), num_of_posts = 3) #else get posts from rand group
                        not_used_accounts = tokens
                        not_used_accounts.remove(choosed_account)
                        time_print.t_print('Sending something to friend')
                        vk, info = Vk_logic.autorisation(not_used_accounts[randint(0,len(not_used_accounts)-1)])
                        succesful_done = Vk_logic.send_to_friend(choosed_account, info[3], str(rand_group[0]), posts, message = post_comments[randint(0,len(post_comments)-1)])
                    except:
                        succesful_done = False
                if rand_action in range(90,101):   #from 9 to 11, 20% chance to repost something on wall
                    time_print.t_print('Trying to repost something on wall')
                    time_print.t_print('Getting a random group')
                    rand_group = life_emit_class.rand_new_object(Vk_logic.get_groups(choosed_account), used_groups)
                    time_print.t_print('Collecting posts')
                    try:
                        posts = Vk_logic.get_posts(token=choosed_account, group_id=str(rand_group[0]), num_of_posts = 3) #else get posts from rand group
                        time_print.t_print('Reposting something on wall')
                        succesful_done = Vk_logic.repost_on_wall(choosed_account, str(rand_group[0]), posts)
                    except:
                        succesful_done = False
                if succesful_done:
                    last_launch = datetime.datetime.now()
                    main_lock.acquire()
                    system_variables['last_life_emiting'] = datetime.datetime.now()
                    main_lock.release()
                    time_print.t_print('Succesful made an life emiting action', color = 'g')
                    main_lock.acquire()
                    file_settings['life_emit_online'] = 0
                    main_lock.release()
                    auto_cycles.saving_settings(file_settings, system_variables)
                if not(succesful_done):
                    time_print.t_print('Trying to make new life emiting action')
            if checked_messages == False and datetime.datetime.now() >= last_launch + datetime.timedelta(minutes = latency//2) and not(system_variables['message_send_online']) and not(system_variables['post_creator_online']): #if its time to make this shit
                checked_messages = True
                main_lock.acquire()
                system_variables['life_emit_online'] = 1
                main_lock.release()
                for i, token in enumerate(all_tokens):
                    time_print.t_print('Cheking {0} account on new messages'.format(str(i+1)))
                    not_used_accounts = all_tokens.copy()
                    not_used_accounts.remove(token)
                    for tk in not_used_accounts:
                        vk, info = Vk_logic.autorisation(tk)
                        Vk_logic.answer_on_message(token, info, message = message_answers[randint(0,len(message_answers)-1)])
                answer_on_friendly_mes = True
                main_lock.acquire()
                system_variables['life_emit_online'] = 0
                main_lock.release()

class auto_sending_class:

    def rand_new_group(group_ids, used_id):
        if len(used_id) >= (len(group_ids)// 2):
            used_id.pop(0)
        while True:
            rand_new_id = group_ids[randint(0, len(group_ids)-1)]
            try:
                int_ = int(rand_new_id)
            except:
                continue
            if rand_new_id in used_id:
                continue
            if not(rand_new_id in used_id):
                used_id.append(rand_new_id)
                break
        return rand_new_id

    def main_cycle(group_ids_orig, protected_group_id_orig):
        time.sleep(10)
        global file_settings, system_variables, messages, main_lock
        for part_groups in group_ids_orig:
            for group_id in part_groups:
                if len(group_id) < 1:
                    part_groups.remove(group_id)
        all_tokens = file_settings['message_tokens_1'].split(';')
        all_dop_tokens =file_settings['message_tokens_2'].split(';')
        used_ids = []
        time_print.t_print('Getting system variables for autosending')
        last_launch =  system_variables['last_sending']
        latency  = file_settings['auto_sending_timer']
        message_count_1 = file_settings['message_count_1']
        message_count_2 = file_settings['message_count_2']
        main_message = messages[0]
        dop_message = messages[1]
        double_sending = file_settings['double_sending']
        main_lock.acquire()
        system_variables['message_send_worker'] = 1 #signal that auto-sending working
        main_lock.release()
        main_part = True
        while file_settings['auto_sending']:
            if datetime.datetime.now() >= last_launch + datetime.timedelta(days = latency) and not(system_variables['life_emit_online']) and not(system_variables['post_creator_online']): #if its time to send this shit
                main_lock.acquire()
                system_variables['message_send_online'] = 1
                main_lock.release()
                if double_sending:
                    if main_part:
                        group_ids = group_ids_orig[0]
                        protected_group_id = protected_group_id_orig[0]
                        tokens = all_tokens.copy()
                        count = 30 + len(tokens)*20
                        message = main_message
                        message_count = int(message_count_1)
                        time_print.t_print('Launching Main sending', color = 'g')
                    if not(main_part):
                        group_ids = group_ids_orig[1]
                        protected_group_id = protected_group_id_orig[1]
                        tokens = all_dop_tokens.copy()
                        count = 30 + len(tokens)*20
                        message = dop_message
                        message_count = int(message_count_2)
                        time_print.t_print('Launching Additional sending', color = 'g')
                if not(double_sending):
                    group_ids = group_ids_orig[0]
                    protected_group_id = protected_group_id_orig[0]
                    tokens = all_tokens.copy()
                    message_count = int(message_count_1)
                    time_print.t_print('Launching new sending', color = 'g')
                all_send_ids = []
                all_message_ids = []
                time_print.t_print('Getting random group from choosed')
                rand_group_id = auto_sending_class.rand_new_group(group_ids=group_ids, used_id=used_ids) #take a random group id from all
                not_members = []
                time_print.t_print('Cheking accounts')
                for token in tokens:
                    if Vk_logic.autorisation(token=token) == None: #if account got banned delete it
                        tokens.remove(token)
                        time_print.t_print('Found a banned account', color = 'y')
                    if Vk_logic.autorisation(token=token) != None:
                        continue
                for token in tokens:
                    try:
                        posts = Vk_logic.get_posts(token=token, group_id=rand_group_id, num_of_posts = message_count//2) #get posts from rand group
                        if len(posts) < 1:
                            continue
                        if len(posts) >= 1:
                            time_print.t_print('Getting posts')
                            for i, post_id in enumerate(posts):
                                time_print.t_print('Analyzing {0} post'.format(str(i+1)))
                                likes = Vk_logic.get_likes(token=token, group_id=rand_group_id, post_id=post_id) #than get likers ids from posts
                                if len(likes) >= 1:
                                    time_print.t_print('Start deleting members')
                                    non_members = (Vk_logic.is_member_of_group(token=token, group_id=protected_group_id, user_ids=likes, count=count)) #and delete ids if they already subscribed to us
                                    for id in non_members:
                                        not_members.append(id)
                                if len(non_members) >= count:
                                    break
                            break
                    except Exception as e:
                        time_print.t_print(str(e), color = 'r')
                        continue
                time_print.t_print('Deleting account which already got messages')
                for token in tokens:
                    messages = Vk_logic.get_messages(token=token)
                    all_message_ids.append(messages) #get all ids from message_send_worker
                for id in not_members:
                    if id in all_message_ids:
                        not_members.remove(id) #if we have some id in our messages than we dont need to send message again to it
                mes_id = 0 #id
                sended_messages = 0
                time_print.t_print('Start sending')
                while sended_messages < message_count and mes_id < len(not_members):
                    for token in tokens:
                        succes = Vk_logic.send_message(token=token, user_id=not_members[mes_id], message = message) #trying to send message and if succesful
                        if succes:
                            time_print.t_print('Succesful sended a message to vk.com/id{0}'.format(not_members[mes_id]))
                            sended_messages += 1
                            mes_id += 1
                            continue
                        if not(succes):
                            time_print.t_print('Impossible to send a message to vk.com/id{0}'.format(not_members[mes_id]), color = 'y')
                            mes_id += 1 #else just go to the next mes_id
                            continue
                last_launch = datetime.datetime.now()
                main_lock.acquire()
                system_variables['last_sending'] = datetime.datetime.now()
                main_lock.release()
                if double_sending:
                    main_part = not(main_part)
                time_print.t_print('Succesful sended {0} messages'.format(str(sended_messages)), color = 'g')
                main_lock.acquire()
                system_variables['message_send_online'] = 0
                main_lock.release()
                auto_cycles.saving_settings(file_settings, system_variables)
            if datetime.datetime.now() < last_launch + datetime.timedelta(days = latency):
                deff = last_launch+ datetime.timedelta(minutes = latency) - datetime.datetime.now()
                days, seconds = deff.days, deff.seconds
                hours = str(days * 24 + seconds // 3600)
                minutes = str((seconds % 3600) // 60)
                seconds = str((seconds % 60))
                main_lock.acquire()
                system_variables['before_new_launch'] = '{0}:{1}:{2}'.format(hours, minutes, seconds)
                main_lock.release()
                time.sleep(10)

class post_making_class:

    def rand_new_word(all_words, used_words):
        if len(used_words) >= (len(all_words)// 2):
            used_words.pop(0)
        while True:
            rand_new_words = all_words[randint(0, len(all_words)-1)].replace('\n', '')
            if rand_new_words in used_words:
                continue
            if not(rand_new_words in used_words):
                used_words.append(rand_new_words)
                break
        return rand_new_words

    def main_cycle(self, token, post_group_id):
        global file_settings, system_variables, messages
        time.sleep(10)
        used_add_words = []
        used_main_words = []
        last_launch =  system_variables['last_post_creating']
        smiles_for_posts = '😄🙃😊😁😍🤩🥰☺😜😌🤤😎😝😋😏🥵🔥🌈⭐✨🌺🌼🌷🌿💕💞💓💘'
        latency  = file_settings['auto_posting_timer']
        publish_latency = file_settings['publish_latency']
        post_adding_title = messages[2]
        main_lock.acquire()
        system_variables['post_creator_worker'] = 1
        main_lock.release()
        try:
            all_add_wrods = open('add_words.txt', 'r', encoding='utf8').readlines()
        except:
            all_add_wrods  = ''
        try:
            all_main_wrods = open('main_words.txt', 'r', encoding='utf8').readlines()
        except:
            all_main_wrods  = ''
        while file_settings['auto_posting']:
            if datetime.datetime.now() >= last_launch + datetime.timedelta(minutes = latency) and not(system_variables['message_send_online']) and not(system_variables['life_emit_online']):
                main_lock.acquire()
                system_variables['post_creator_online'] = 1
                main_lock.release()
                time_print.t_print('Creating new post', color = 'g')
                abjective_word = post_making_class.rand_new_word(all_add_wrods, used_add_words)
                main_word = post_making_class.rand_new_word(all_main_wrods, used_main_words)
                try:
                    links = image_worker.images_for_post(main_word, abjective_word)
                except Exception as e:
                    time_print.t_print('Got an Error '+str(e), color = 'r')
                    continue
                if links == None:
                    continue
                vk_photo_ids = []
                vk_photo_owner_id = 0
                print(links)
                for i, link in enumerate(links):
                    time_print.t_print('Loading {0} image to album'.format(str(i+1)))
                    vk_photo_ids.append(Vk_logic.upload_photos_to_new_album(token, 'Photos for Posts', link)[1])
                    vk_photo_owner_id = Vk_logic.upload_photos_to_new_album(token, 'Photos for Posts', link)[2]
                try:
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    unix_timestamp = current_time.timestamp()
                    vk_unixtime = unix_timestamp + (publish_latency*60)
                except:
                    vk_unixtime = 0
                print(vk_photo_ids)
                post_title = main_word+smiles_for_posts[randint(0, len(smiles_for_posts)-1)]+'\n'+'#'+main_word.replace(' ', '_')+'\n'+post_adding_title
                if len(vk_photo_ids) > 0:
                    Vk_logic.create_post(token, post_group_id, vk_photo_owner_id, vk_photo_ids, post_title, vk_unixtime)
                    last_launch = datetime.datetime.now()
                    system_variables['last_post_creating'] = datetime.datetime.now()
                    time_print.t_print('Succesful created a new post', color = 'g')
                    main_lock.acquire()
                    system_variables['post_creator_online'] = 0
                    main_lock.release()
                    auto_cycles.saving_settings(file_settings, system_variables)
                if len(vk_photo_ids) <= 0:
                    time_print.t_print('Pictures wasnt downloaded, trying new theme', color = 'y')

class auto_cycles():
    def logs_del():
        log_names = os.listdir('Logs/') #clear the logs
        for name in log_names:
            date = datetime.datetime.strptime(name.split('.txt')[0], "%Y-%m-%d")
            if datetime.datetime.now() >= date + datetime.timedelta(days = 14):
                    os.remove('Logs/'+name)
    def saving_settings(file_settings, system_variables):
        file = open('settings.json', 'w', encoding='utf8')
        for item in file_settings.items():
            file.write(item[0]+' = '+str(item[1])+'\n')
        file.close()
        file = open('sys_variables.json', 'w', encoding='utf8')
        for item in system_variables.items():
            if item[0] == 'last_sending' or item[0] == 'last_life_emiting' or item[0] == 'last_post_creating' or item[0] == 'last_auto_restart':

                file.write(item[0]+' = '+datetime.datetime.strftime(item[1], "%Y-%m-%d %H:%M:%S.%f")+'\n')
            else:
                file.write(item[0]+' = '+str(item[1])+'\n')
        file.close()
    def main(self):
        global file_settings, system_variables, main_lock
        global auto_send, life_emiting, auto_post
        main_lock.acquire()
        system_variables['auto_restart_worker'] = 1
        main_lock.release()
        last_set_saving = datetime.datetime.now()
        last_log_deleting = datetime.datetime.strptime('2021-05-05', "%Y-%m-%d")
        last_life_emit_online, last_message_sender_online, last_post_creator_online =0,0,0
        start_time_life_emit, start_time_post_creator, start_time_message_sender = datetime.datetime.now(), datetime.datetime.now(), datetime.datetime.now()
        auto_rest_timer = file_settings['auto_restart_timer']
        last_auto_restart = system_variables['last_auto_restart']
        while file_settings['additional_tasks']:
            #==========================LOGS DELETING==========================#
            if datetime.datetime.now() >= last_log_deleting + datetime.timedelta(days = 1):
                time_print.t_print('Deleting old logs', color = 'c')
                auto_cycles.logs_del()
                last_log_deleting = datetime.datetime.now()
            #==========================SETTINGS SAVING==========================#
            if datetime.datetime.now() >= last_set_saving + datetime.timedelta(minutes = 5):
                time_print.t_print('Auto-saving settings', color = 'c')
                auto_cycles.saving_settings(file_settings, system_variables)
                last_set_saving = datetime.datetime.now()
            #==========================AUTO RESTARTING==========================#
            was_restarting = False
            message_send_worker, life_emit_worker, post_creator_worker = system_variables['message_send_worker'], system_variables['life_emit_worker'], system_variables['post_creator_worker']
            message_sender_online, life_emit_online, post_creator_online = system_variables['message_send_online'], system_variables['life_emit_online'], system_variables['post_creator_online']
            if not(last_life_emit_online) and life_emit_online:
                start_time_life_emit = datetime.datetime.now()
            if not(last_message_sender_online) and message_sender_online:
                start_time_message_sender = datetime.datetime.now()
            if not(last_post_creator_online) and post_creator_online:
                start_time_post_creator = datetime.datetime.now()
            if life_emit_worker and last_life_emit_online and life_emit_online and datetime.datetime.now() >= start_time_life_emit + datetime.timedelta(minutes = 30) and auto_rest_timer == 0: #if last launch was 30 minutes ago, and still 'online', than restart it
                time_print.t_print('Restarting "Life Emit" cycle', color = 'c')
                try:
                    life_emiting.join()
                except:
                    pass
                main_lock.acquire()
                system_variables['life_emit_worker'] = 0
                main_lock.release()
                was_restarting = True
                life_emit_online = 0
            if message_send_worker and last_message_sender_online and message_sender_online and datetime.datetime.now() >= start_time_message_sender + datetime.timedelta(minutes = 30) and auto_rest_timer == 0: #if last launch was 30 minutes ago, and still 'online', than restart it
                time_print.t_print('Restarting "Message Sending" cycle', color = 'c')
                try:
                    auto_send.join()
                except:
                    pass
                main_lock.acquire()
                system_variables['message_send_worker'] = 0
                main_lock.release()
                was_restarting = True
                message_sender_online = 0
            if post_creator_worker and last_post_creator_online and post_creator_online and datetime.datetime.now() >= start_time_post_creator + datetime.timedelta(minutes = 60) and auto_rest_timer == 0: #if last launch was 30 minutes ago, and still 'online', than restart it
                time_print.t_print('Restarting "Post Creating" cycle', color = 'c')
                try:
                    auto_post.join()
                except:
                    pass
                main_lock.acquire()
                system_variables['post_creator_worker'] = 0
                main_lock.release()
                was_restarting = True
                post_creator_online = 0
            if auto_rest_timer != 0:
                if datetime.datetime.now() >= last_auto_restart + datetime.timedelta(minutes = auto_rest_timer):
                    time_print.t_print('Restarting all cycles by time', color = 'c')
                    main_lock.acquire()
                    file_settings['life_emit'] = 0
                    system_variables['life_emit_worker'] = 0
                    file_settings['auto_sending'] = 0
                    system_variables['message_send_worker'] = 0
                    file_settings['auto_posting'] = 0
                    system_variables['post_creator_worker'] = 0
                    main_lock.release()
                    time.sleep(300)
                    was_restarting = True
                    last_auto_restart = datetime.datetime.now()
                    main_lock.acquire()
                    system_variables['last_auto_restart'] = datetime.datetime.now()
                    main_lock.release()
            if was_restarting:
                main_lock.acquire()
                system_variables['restart_server'] = 1
                main_lock.release()
            last_life_emit_online, last_message_sender_online, last_post_creator_online = life_emit_online, message_sender_online, post_creator_online

class main:
    def main():
        global file_settings, system_variables, messages, group_data
        global auto_send, life_emiting, auto_post, additional_cycles
        file_settings = copy.deepcopy(settings.get_settings())
        system_variables = copy.deepcopy(settings.get_settings(file_name = 'sys_variables.json'))
        group_data = copy.deepcopy(settings.get_groups_data())
        messages = [settings.get_message(), settings.get_message(file_message = 'message_2.txt'), settings.get_message(file_message = 'post_message.txt') ]
        system_variables['auto_restart_worker'] = 0
        system_variables['life_emit_worker'] = 0
        system_variables['message_send_worker'] = 0
        system_variables['post_creator_worker'] = 0
        system_variables['life_emit_online'] = 0
        system_variables['message_send_online'] = 0
        system_variables['post_creator_online'] = 0
        system_variables['restart_server'] = 0
        while True:
            if system_variables['stop_server']:
                system_variables['stop_server'] = 0
                auto_cycles.saving_settings(file_settings, system_variables)
                time_print.t_print('Manager Shutting Down', color = 'y')
                break
                continue
            time_print.t_print('Getting system variables')
            main_token = file_settings['main_token']
            op_ids = file_settings['op_ids'].split(';')
            tokens = file_settings['all_tokens'].split(';')
            time_print.t_print('Getting account tokens')
            deleting_tokenks = []
            for i, token in enumerate(tokens):
                try:
                    if len(token) < 4:
                        deleting_tokenks.append(token)
                        continue
                    vk, info = Vk_logic.autorisation(token= token)
                    time_print.t_print('Cheking {0} {1} account'.format(info[1], info[2]))
                except:
                    deleting_tokenks.append(token)
                    time_print.t_print('{0} account get banned'.format(str(i+1)), color = 'y')
                    continue
            for token in deleting_tokenks:
                tokens.remove(token)
            try:
                vk, info = Vk_logic.autorisation(token= main_token)
                time_print.t_print('Cheking {0} {1} main account'.format(info[1], info[2]))
            except:
                time_print.t_print('Main account got banned or does not exist', color = 'y')
                if len(tokens) > 0:
                    main_token = tokens[0]
                    vk, info = Vk_logic.autorisation(token= main_token)
                    time_print.t_print('Alternative main account choosed as {0} {1}'.format(info[1], info[2]), color = 'y')
                    for id in op_ids:
                        try:
                            Vk_logic.send_fast(token=main_token, user_id=str(id), message = 'Проблема со входом в главный аккаунт, данный аккаунт выбран как резервный')
                        except:
                            continue
                if len(tokens) == 0:
                     main_token = ''
            time_print.t_print('Getting password: '+system_variables['password'])
            time_print.t_print('Getting groups data')
            choose_groups = [group_data['group_ids_1'].split(';'),group_data['group_ids_2'].split(';')]
            choose_prot_group = [group_data['protected_group_id_1'],group_data['protected_group_id_2']]
            post_group_id = group_data['post_group_id']
            time_print.t_print('Getting cycle variables')
            if main_token == '':
                time_print.t_print('Asking about main account token')
                settings.set_settings(setting_name = 'main_token', setting_value = input('Введите токен аккаунта, который будет использоваться как главный: '))
                continue

            if file_settings['auto_sending'] and not(system_variables['message_send_worker']):
                time_print.t_print('Launching auto_sending cycle', color = 'g')
                auto_send = threading.Thread(target = auto_sending_class.main_cycle , daemon=True, args = (choose_groups, choose_prot_group))
                auto_send.start()
                time.sleep(1)
            elif system_variables['message_send_worker']:
                time_print.t_print('Auto sending cycle already running', color = 'y')
            if file_settings['life_emit'] and not(system_variables['life_emit_worker']):
                time_print.t_print('Launching life emitting cycle', color = 'g')
                life_emiting = threading.Thread(target = life_emit_class.main_cycle , daemon=True, args=('1', tokens))
                life_emiting.start()
                time.sleep(1)
            elif system_variables['life_emit_worker']:
                time_print.t_print('Life emiting cycle already running', color = 'y')
            if file_settings['auto_posting'] and not(system_variables['post_creator_worker']):
                time_print.t_print('Launching post creating cycle', color = 'g')
                auto_post = threading.Thread(target = post_making_class.main_cycle , daemon=True, args=('1', main_token, post_group_id))
                auto_post.start()
                time.sleep(1)
            elif system_variables['post_creator_worker']:
                time_print.t_print('Auto post creating cycle already running', color = 'y')
            if file_settings['additional_tasks'] and not(system_variables['auto_restart_worker']):
                time_print.t_print('Launching additional tasks cycle', color = 'g')
                additional_cycles = threading.Thread(target = auto_cycles.main , daemon=True, args=('1'))
                additional_cycles.start()
            elif system_variables['auto_restart_worker']:
                time_print.t_print('Additional tasks cycle already running', color = 'y')
            time_print.t_print('Manager Online', color = 'g')
            while True:
                server_restart = system_variables['restart_server']
                if server_restart:
                    system_variables['restart_server'] = 0
                    if not(system_variables['stop_server']):
                        time_print.t_print('Manager restarting', color = 'y')
                        auto_cycles.saving_settings(file_settings, system_variables)
                    break
                    continue
                command_class.command_taker(main_token, tokens, password = system_variables['password'])

if __name__ == '__main__':

    main.main()
