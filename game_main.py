import numpy 
import telebot
import logging
from pandas.plotting import table 
import matplotlib.pyplot as plt
import pandas
import sqlite3
import sys

import game_folder.generate_dungeon


class game_control:
    """docstring for game_control"""
    def __init__(self):
        self.user_id = 0
        self.character = Player()
        self.monster = Player()
        self.creating_character = False
        self.veteran_character = False
        self.last_status = 0
        self.complete = False
        self.dead = False
        self.dungeon = []
        self.creators = 0
        self.doom = 0
        self.x = 0; self.y = 0
        self.in_room_now = 0
        self.has_map = False
        self.is_being_teleported = False
        self.is_fighting = False
        self.fighting_counter = 4

    def choose_class(self, new_class):
        new_class.name = self.character.name 
        new_class.race = self.character.race
        new_class.role = self.character.role
        new_class.set_stats(self.character.strength, self.character.intellect, self.character.endurance)
        new_class.inventory = self.character.inventory
        new_class.score = self.character.score
        self.character = new_class
        


    def how_many_rooms_left(self):
        temp = len(self.dungeon)
        for i in range(len(self.dungeon)):
            if self.dungeon[i].is_cleared:
                temp -= 1
        return temp

    def check_completion(self):
        if self.dungeon[-1].is_cleared and self.complete == False:
            self.complete = True
            self.character.calculate_score()

    def determine_possible_moves(self):
        temp = []
        room = self.dungeon[self.in_room_now]
        for i in range(len(room.neighbours)):
            if room.neighbours[i] != ' ':
                next_room = self.dungeon[room.neighbours[i]]
                if room.coord_x > next_room.coord_x:
                    temp.append(u'\U00002B05')
                if room.coord_y > next_room.coord_y:
                    temp.append(u'\U00002B07')
                if room.coord_y < next_room.coord_y:
                    temp.append(u'\U00002B06')
                if room.coord_x < next_room.coord_x:
                    temp.append(u'\U000027A1')
                
        return temp

    def move(self, message):
        if message == u'\U00002B05':
            self.x -= 1
        if message == u'\U000027A1':
            self.x += 1
        if message == u'\U00002B07':
            self.y -= 1
        if message == u'\U00002B06':
            self.y += 1
        for i in range(len(self.dungeon)):
            if self.dungeon[i].coord_x == self.x \
            and self.dungeon[i].coord_y == self.y:

                self.in_room_now = self.dungeon[i].room_id
                if self.dungeon[self.in_room_now].is_cleared == False \
                and self.in_room_now != self.dungeon[-1].room_id:
                    self.check_for_monster()
                self.dungeon[self.in_room_now].is_cleared = True


    def teleport(self, where_to):
        if where_to > self.dungeon[-1].room_id or where_to < 0:
            raise
        else:
            for i in range(len(self.dungeon)):
                if self.dungeon[i].room_id == where_to:
                    self.x = self.dungeon[i].coord_x
                    self.y = self.dungeon[i].coord_y
                    self.in_room_now = self.dungeon[i].room_id
                    self.is_being_teleported = False
                    self.dungeon[i].is_cleared = True

                    if self.in_room_now != self.dungeon[-1].room_id:
                        self.check_for_monster()

                    for j in range(len(self.character.inventory)):
                        if self.character.inventory[j].description == 'scroll of teleportation':
                            self.character.inventory.pop(j)
                            break
                    break


    def check_for_monster(self):
        if self.dungeon[self.in_room_now].has_monster:
            self.is_fighting = True
            self.fighting_counter = 4
            self.dungeon[self.in_room_now].has_monster = False
        else:
            self.fighting_counter -= 1
            roll = numpy.random.randint(low=0, high=4)
            if roll > self.fighting_counter:
                self.is_fighting = True
                self.fighting_counter = 4


    def clean(self):
        self.user_id = 0
        self.character = Player()
        self.monster = Player()
        self.creating_character = False
        self.last_status = 0
        self.complete = False
        self.dead = False
        self.dungeon = []
        self.creators = 0
        self.x = 0; self.y = 0
        self.in_room_now = 0
        self.has_map = False
        self.is_being_teleported = False
        self.is_fighting = False

class Player:
    """docstring for Player"""
    def __init__(self):
        self.name = '____no_name____'
        self.race = 'human'
        self.role = 'warrior'
        self.strength = 50
        self.intellect = 50
        self.endurance = 50
        self.hp = 5
        
        # For monsters: 0 = no monster; 1 = active monster; 2 = stunned monster
        self.score = 0 
        self.inventory = []
        

    def show_inventory(self):
        temp = []
        for i in range(len(self.inventory)):
            temp.append(self.inventory[i].inventory_line())
        return temp

    def add_to_inventory(self, items):
        for i in range(len(items)):
            if items[i].type == 'score':
                self.score += items[i].equip()
            else:
                if items[i].type == 'stats':
                    self.score += 2
                self.inventory.append(items[i])


    def take_from_inventory(self, desc):
        for i in range(len(self.inventory)):
            if desc == self.inventory[i].description:
                return self.inventory[i]

    def use(self, item):
        for i in range(len(self.inventory)):
            if item == self.inventory[i].description:
                effect, add = self.inventory[i].use()
                self.inventory.pop(i)
                if effect == 'strength': 
                    self.strength += add
                    return item+' increased your '+effect+' by '+str(add)
                if effect == 'intellect': 
                    self.intellect += add
                    return item+' increased your '+effect+' by '+str(add)
                if effect == 'endurance': 
                    self.endurance += add
                    return item+' increased your '+effect+' by '+str(add)
                if effect == 'healing':
                    self.heal(add)
                    return 'You have healed. Your current hp: '+str(self.hp)


    def heal(self, hp):
        hp_max = int(self.endurance/10) + 1
        if (self.hp + hp) >= hp_max:
            self.hp = hp_max
        else:
            self.hp += hp

    def set_stats(self, strength, intellect, endurance):
        self.strength = strength
        self.intellect = intellect
        self.endurance = endurance
        self.hp = int(endurance/10) + 1

    def set_name(self, name):
        self.name = name

    def set_max_hp(self):
        self.hp = int(self.endurance/10) + 1

    def calculate_score(self):
        self.score += 0.1*self.endurance
        if self.role == 'warrior':
            self.score += 0.1*self.strength+0.2*self.intellect
        elif self.role == 'mage':
            self.score += 0.2*self.strength+0.1*self.intellect
        self.score = int(self.score)

    def set_up_monster(self, monster):
        self.score = 1
        self.name = monster[0] #description
        self.race = monster[1] #class
        self.hp = monster[2] 
        self.strength = monster[3][0] 
        self.intellect = monster[3][1]
        self.endurance = monster[3][2]
        self.role = monster[4]

    def save_character(self, user_id, folder=''):
        inventory = ''
        for i in range(len(self.inventory)):
            inventory += self.inventory[i].save_line()
            inventory += '\n'

        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO characters VALUES (?,?,?,?,?,?,?,?,?)', 
            (user_id, self.name, self.race, self.role, self.strength, self.intellect, self.endurance, self.score, inventory))
        conn.commit()
        conn.close()

    def load_character(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM characters WHERE user_id = ? LIMIT 1', [user_id]) 
        temp = c.fetchall() 
        conn.close()

        temp = temp[0]
        self.name = temp[1]
        self.race = temp[2]
        self.role = temp[3]
        self.set_stats(temp[4], temp[5], temp[6])
        self.score = temp[7]

        inventory = temp[8].split(';\n')
        result = []
        for i in range(len(inventory)-1):
            temp = inventory[i].split('\n')
            x = game_folder.generate_dungeon.Item()
            x.description = temp[0].split(' = ')[1]
            x.type = temp[1].split(' = ')[1]
            x.effect = temp[2].split(' = ')[1]
            x.add = int(temp[3].split(' = ')[1])
            result.append(x)

        self.add_to_inventory(result)

    def delete_character(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('DELETE FROM characters WHERE user_id = ? LIMIT 1', [user_id])
        conn.commit()
        conn.close()


class Warrior(Player):
    has_used_second_breath = False
    stun_cooldown = 5

    def second_breath(self):
        if self.has_used_second_breath == False:
            roll = numpy.random.randint(low=2, high=5)
            self.heal(roll)
            self.has_used_second_breath = True
            return 'You have healed '+str(roll)+' hp.\nYour current hp: '+str(self.hp)
        else:
            return 0

    def stun(self):
        if self.stun_cooldown == 5:
            self.stun_cooldown = 4
            return 'stun'

    def update(self):
        temp = [0,0]
        if self.stun_cooldown == 5:
            temp[1] = 'Stun attack: stuns opponent for 1 round'
        if self.stun_cooldown != 5 and self.stun_cooldown != 0:
            self.stun_cooldown -= 1
            temp[1] = 'CD: '+str(self.stun_cooldown)
        if self.stun_cooldown == 0:
            self.stun_cooldown = 5
            temp[1] = 'Stun attack: stuns opponent for 1 round'

        if self.has_used_second_breath:
            temp[0] = 'Used'
        else:
            temp[0] = 'Second breath: heals 2-4 hp'

        return temp


class Mage(Player):
    has_used_healing = False
    fireball_cooldown = 5

    def healing(self):
        if self.has_used_healing == False:
            roll = numpy.random.randint(low=2, high=4)
            self.heal(roll)
            self.has_used_healing = True
            return 'You have healed '+str(roll)+' hp.\nYour current hp: '+str(self.hp)
        else:
            return 0

    def fireball(self):
        if self.fireball_cooldown == 5:
            self.fireball_cooldown = 4
            return 'fireball'

    def update(self):
        temp = [0,0]
        if self.fireball_cooldown == 5:
            temp[1] = 'Fireball: deals 3 damage'
        if self.fireball_cooldown != 5 and self.fireball_cooldown != 0:
            self.fireball_cooldown -= 1
            temp[1] = 'CD: '+str(self.fireball_cooldown)
        if self.fireball_cooldown == 0:
            self.fireball_cooldown = 5
            temp[1] = 'Fireball: deals 3 damage'

        if self.has_used_healing:
            temp[0] = 'Used'
        else:
            temp[0] = 'Healing spell: heals 2-3 hp'

        return temp

        


game_user = []




def show_status(bot, message):
    global game_user

    k = 9000
    user_id = message.from_user.id
    for i in range(len(game_user)):
        if game_user[i].user_id == user_id:
            k = i
            break

    if k == 9000 or game_user[k].character.name == "____no_name____":
        bot.send_message(message.chat.id, 'First create your character')
    else:
        character_text = 'Name: '+game_user[k].character.name+\
        '\nRace: '+game_user[k].character.race+'\nClass: '+game_user[k].character.role+'\nStrength: '+str(game_user[k].character.strength)+\
        '\nIntellect: '+str(game_user[k].character.intellect)+'\nEndurance: '+str(game_user[k].character.endurance)+\
        '\nHealth: '+str(game_user[k].character.hp)+'\nScore: '+str(int(game_user[k].character.score))
        bot.send_message(message.chat.id, character_text)


def spawn_item(description, it_type='consumable', effect='healing', add=1):
    x = game_folder.generate_dungeon.Item()
    x.description = description
    x.type = it_type
    x.effect = effect
    x.add = add
    return x



def clean_history(message):
    global game_user

    user_id = message.from_user.id
    for i in range(len(game_user)):
        if game_user[i].user_id == user_id:
            game_user[i].clean()
            game_user.pop(i)
            break


def create_character(bot, message, start):
    global game_user
    status_change = True

    conn = sqlite3.connect('game_folder/character_save.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM characters WHERE user_id = ? LIMIT 1', [message.from_user.id]) 
    temp = c.fetchall() 
    conn.close()

    if len(temp) == 1:
        game_user.append(game_control())
        game_user[-1].creating_character = True
        game_user[-1].veteran_character = True
        game_user[-1].user_id = message.from_user.id
        game_user[-1].character.load_character(message.from_user.id, folder='game_folder/')
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row('Yes', 'No')
        bot.send_message(message.chat.id, 'You have the following saved character:', reply_markup=keyboard)
        show_status(bot, message)
        bot.send_message(message.chat.id, 'Do you want to play as this character (yes) or create a new one (no)?\nIf you choose to create a new one, old character will be deleted.')
        return 0

    #fix player slot
    start_new_game_flag = False
    user_id = message.from_user.id
    k = 9000
    for i in range(len(game_user)):
        if game_user[i].user_id == user_id:
            k = i

    if k == 9000:
        game_user.append(game_control())
        start_new_game_flag = True
        game_user[-1].user_id = user_id
        k = -1

    game_user[k].creating_character = True

    if start: start_new_game_flag = True

    if start_new_game_flag:
        bot.send_message(message.chat.id, 'Enter character name:')
    else:
        text = message.text
        if text.lower() in ['human', 'elf', 'dwarf', 'ork'] and game_user[k].last_status == 1:
            text = text.lower()
            game_user[k].character.race = text

            if text == 'elf':
                game_user[k].character.strength = 45
                game_user[k].character.intellect = 55

            if text == 'dwarf':
                game_user[k].character.strength = 45
                game_user[k].character.endurance = 55

            if text == 'ork':
                game_user[k].character.strength = 55
                game_user[k].character.intellect = 45

            choose_role_text = 'Next select a class:'
            keyboard_role = telebot.types.ReplyKeyboardMarkup(True)
            keyboard_role.row('warrior', 'mage')
            bot.send_message(message.chat.id, choose_role_text, reply_markup=keyboard_role)
        elif text.lower() in ['warrior', 'mage'] and game_user[k].last_status == 1:
            text = text.lower()
            game_user[k].character.role = text
            game_user[k].character.set_max_hp()

            if text == 'warrior':
                game_user[k].character.strength += 5
                game_user[k].choose_class(Warrior())

            if text == 'mage':
                game_user[k].character.intellect += 5
                game_user[k].choose_class(Mage())

            game_user[k].last_status = 0
            character_created_text = 'Congratulations, your character is created!\nName: '+game_user[k].character.name+\
            '\nRace: '+game_user[k].character.race+'\nClass: '+game_user[k].character.role+'\nStrength: '+str(game_user[k].character.strength)+\
            '\nIntellect: '+str(game_user[k].character.intellect)+'\nEndurance: '+str(game_user[k].character.endurance)+\
            '\nHealth: '+str(game_user[k].character.hp)
            keyboard_1 = telebot.types.ReplyKeyboardMarkup(True)
            keyboard_1.row('Next')
            bot.send_message(message.chat.id, character_created_text, reply_markup=keyboard_1)
            status_change = False
            logging.info(message.from_user.first_name+' created a character')
        elif game_user[k].last_status == 0:
            if game_user[k].character.name == '____no_name____':
                game_user[k].character.set_name(text)
                game_user[k].last_status = 1
                choose_race_text = 'Now choose race:'
                keyboard_race = telebot.types.ReplyKeyboardMarkup(True)
                keyboard_race.row('human', 'elf', 'dwarf', 'ork')
                bot.send_message(message.chat.id, choose_race_text, reply_markup=keyboard_race)
            else:
                bot.send_message(message.chat.id, 'Your character died during birth.')
                game_user[k].clean()
                game_user.pop(k)
        else:
            bot.send_message(message.chat.id, 'Use only options available on buttons.')

    return status_change


def game(bot, message):
    global game_user
    logging.info('')

    k = 9000
    user_id = message.from_user.id
    for i in range(len(game_user)):
        if game_user[i].user_id == user_id:
            k = i
            break

    if k == 9000:
        logging.warning('Unprecidented error occured')

    if game_user[k].creating_character:
        if message.text.lower() == 'yes' and game_user[k].veteran_character:
            game_user[k].creating_character = False
            if game_user[k].character.role == 'warrior':
                game_user[k].choose_class(Warrior())
            if game_user[k].character.role == 'mage':
                game_user[k].choose_class(Mage())

            keyboard = telebot.types.ReplyKeyboardMarkup(True)
            keyboard.row('Next')
            bot.send_message(message.chat.id, 'Adventures of '+game_user[k].character.name+' continues!',reply_markup=keyboard)
            return 0 
        if message.text.lower() == 'no' and game_user[k].veteran_character:
            game_user[k].character.delete_character(message.from_user.id, folder='game_folder/')
            create_character(bot,message,True)
            return 0

        status_change = create_character(bot, message, False)
        game_user[k].creating_character = status_change

        if status_change == False:
            # trying to get some item from storage
            temp = game_folder.generate_dungeon.Item()
            result = temp.transfer_from_storage(message.from_user.id, folder='game_folder/')
            if result == 'success':
                game_user[k].character.add_to_inventory([temp])
                text = 'You have recieved an item left for you by another player.'+\
                '\nIt\'s '+temp.description
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row(u'\U0001F44D','Into the dungeon')
                bot.send_message(message.chat.id, text, reply_markup=keyboard)
        return 0

    if len(game_user[k].dungeon) == 0:

        # rewarding for transfered item
        if len(game_user[k].character.inventory) != 0:
            effect = game_user[k].character.inventory[0].effect.split(',')
            game_user[k].character.inventory[0].effect = effect[0]
            item_type = game_user[k].character.inventory[0].type.split(',')
            game_user[k].character.inventory[0].type = item_type[0]
            if message.text == u'\U0001F44D':
                add_likes(k, bot, message, int(effect[1]), int(item_type[1]), numpy.random.randint(low=46, high=55))
            if message.text.lower() == 'into the dungeon':
                add_likes(k, bot, message, int(effect[1]), int(item_type[1]), numpy.random.randint(low=26, high=35))


        oppening, game_user[k].creators, game_user[k].doom, game_user[k].dungeon = game_folder.generate_dungeon.main(game_user[k].character, folder='game_folder/')
        bot.send_message(message.chat.id, oppening)
        game_folder.generate_dungeon.draw_dungeon(game_user[k].dungeon, [game_user[k].x, game_user[k].y], k, 
                                                    folder='game_folder/', 
                                                    map_found=game_user[k].has_map)
        moves = game_user[k].determine_possible_moves()
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row(*moves)
        keyboard.row('Look around', 'Search', 'Inventory')
        file_name = 'game_folder/dungeon_map_'+str(k)+'.png'
        bot.send_photo(message.chat.id, photo=open(file_name, 'rb'), reply_markup=keyboard)
        bot.send_message(message.chat.id, game_user[k].dungeon[game_user[k].in_room_now].description)
        return 0


    if game_user[k].is_fighting:
        fight(k, bot, message)
        if game_user[k].dead:
            return 1
        else:
            return 0


    if game_user[k].is_being_teleported:
        try:
            game_user[k].teleport(int(message.text))
            text = 'Winds of magic swirl around you as you finish reading the scroll. '+\
            'You open your eyes in completly different place. '+game_user[k].dungeon[game_user[k].in_room_now].description
            game_folder.generate_dungeon.draw_dungeon(game_user[k].dungeon, [game_user[k].x, game_user[k].y], k, 
                                                    folder='game_folder/', 
                                                    map_found=game_user[k].has_map)
            file_name = 'game_folder/dungeon_map_'+str(k)+'.png'
            bot.send_photo(message.chat.id, photo=open(file_name, 'rb'))

            game_user[k].check_completion()
            if game_user[k].complete:
                if len(game_user[k].character.show_inventory()) != 0:
                    text = 'Congratulations! You have completed the dungeon.'+\
                    ' Do you want to help other players and leave one of your items for future adventurers?'
                    keyboard = telebot.types.ReplyKeyboardMarkup(True)
                    keyboard.row('Yes', 'No')
                    bot.send_message(message.chat.id, text, reply_markup=keyboard)
                    return 0
                else:
                    end_game(k, bot, message)
                    return 1

            moves = game_user[k].determine_possible_moves()
            keyboard = telebot.types.ReplyKeyboardMarkup(True)
            keyboard.row(*moves)
            keyboard.row('Look around', 'Search', 'Inventory')
            
            bot.send_message(message.chat.id, text, reply_markup=keyboard)
        except:
            bot.send_message(message.chat.id, 'Enter the number of the room on the map')
        return 0


    if game_user[k].complete:
        if message.text.lower() == 'yes':
            open_inventory(k, bot, message)
            return 0
        elif message.text.lower() == 'no':
            end_game(k, bot, message)
            return 1
        elif message.text in game_user[k].character.show_inventory():
            item = message.text.split(',')[0]
            item = game_user[k].character.take_from_inventory(item)
            item.transfer_to_storage(message.from_user.id, message.chat.id, folder='game_folder/')
            end_game(k, bot, message)
            return 1
        else:
            bot.send_message(message.chat.id, 'Select one of the buttons')


    if message.text.lower() == 'look around':
        bot.send_message(message.chat.id, game_user[k].dungeon[game_user[k].in_room_now].look_around())
        return 0


    if message.text.lower() == 'search':
        items, text = game_user[k].dungeon[game_user[k].in_room_now].loot_room()
        if len(items) != 0: 
            game_user[k].character.add_to_inventory(items)
        bot.send_message(message.chat.id, text)
        return 0


    if message.text.lower() == 'inventory':
        open_inventory(k, bot, message)
        return 0


    if message.text.lower() == 'close':
        moves = game_user[k].determine_possible_moves()
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row(*moves)
        keyboard.row('Look around', 'Search', 'Inventory')
        bot.send_message(message.chat.id, 'Inventory closed', reply_markup=keyboard)
        return 0


    
    if message.text in game_user[k].character.show_inventory():
        item = message.text.split(',')[0]
        if item == 'scroll of teleportation':
            game_user[k].is_being_teleported = True
            text = 'Enter the number of the room to which you wish to be teleported'
            bot.send_message(message.chat.id, text)
            return 0
        elif item == 'map':
            game_user[k].has_map = True
            for i in range(len(game_user[k].character.inventory)):
                if game_user[k].character.inventory[i].description == 'map':
                    game_user[k].character.inventory.pop(i)
            text = 'Now you have a map, you will know the whole layout!'
        else:
            text = game_user[k].character.use(item)

        inventory = game_user[k].character.show_inventory()
        inventory += ['Close']
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        for i in range(len(inventory)):
            item = str(inventory[i])
            keyboard.row(item)
        text += '\n' + game_user[k].character.name + '\'s inventory:' 
        bot.send_message(message.chat.id, text, reply_markup=keyboard)
        return 0 




    moves = game_user[k].determine_possible_moves()
    if message.text in moves:
        game_user[k].move(message.text)
        game_user[k].check_completion()
        n = game_user[k].how_many_rooms_left()

        if game_user[k].complete:
            if len(game_user[k].character.show_inventory()) != 0:
                text = 'Congratulations! You have completed the dungeon.'+\
                ' Do you want to help other players and leave one of your items for future adventurers?'
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row('Yes', 'No')
                bot.send_message(message.chat.id, text, reply_markup=keyboard)
                return 0
            else:
                end_game(k, bot, message)
                return 1

        moves = game_user[k].determine_possible_moves()
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row(*moves)
        keyboard.row('Look around', 'Search', 'Inventory')

        game_folder.generate_dungeon.draw_dungeon(game_user[k].dungeon, [game_user[k].x, game_user[k].y], k, 
                                                    folder='game_folder/', 
                                                    map_found=game_user[k].has_map)
        file_name = 'game_folder/dungeon_map_'+str(k)+'.png'
        bot.send_photo(message.chat.id, photo=open(file_name, 'rb'), reply_markup=keyboard)
        bot.send_message(message.chat.id, game_user[k].dungeon[game_user[k].in_room_now].description+'\nYou have '+str(n)+' more unexplored rooms.')

        if game_user[k].is_fighting:
            fight(k, bot, message)
            if game_user[k].dead:
                return 1

        return 0





    logging.info("Recieved: "+ message.text)


def fight(k, bot, message):
    global game_user

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('Attack')


    if game_user[k].monster.score == 0:
        game_user[k].monster.set_up_monster(game_folder.generate_dungeon.generate_monster(game_user[k].dungeon[game_user[k].in_room_now],
                                                                         game_user[k].creators, 
                                                                         game_user[k].doom,
                                                                         folder='game_folder/'))
        bot.send_message(message.chat.id, 'In the room you see '+game_user[k].monster.name)
        hp_bar = 'Opponents hp: '+'#'*int(game_user[k].monster.hp) + '\n\nYour hp: '+'#'*int(game_user[k].character.hp)
        bot.send_message(message.chat.id, hp_bar)

        abilities = game_user[k].character.update()
        keyboard.row(*abilities)
        bot.send_message(message.chat.id, 'What do you want to do?', reply_markup=keyboard)
    else:
        if message.text.lower() == 'attack':

            # player block
            dmg = numpy.random.randint(low=1, high=3)
            text = ''
            if game_user[k].character.role == 'warrior':
                roll_to_hit = roll(game_user[k].character.strength)
                if roll_to_hit == 0:
                    dmg = 3 #critical hit
                    text = 'It\'s a critical hit! '
                if roll_to_hit < 3:
                    text += 'You slash and deal '+str(dmg)+' damage.'
                    game_user[k].monster.hp -= dmg
                else:
                    text = 'You miss!'
            if game_user[k].character.role == 'mage':
                roll_to_hit = roll(game_user[k].character.intellect)
                if roll_to_hit == 0:
                    dmg = 3 #critical hit
                    text = 'It\'s a critical hit! '
                if roll_to_hit < 3:
                    text += 'You launch magic missiles and deal '+str(dmg)+' damage.'
                    game_user[k].monster.hp -= dmg
                else:
                    text = 'You miss!'


            # monster block
            text = monster_attacks(k, text)

            

            abilities = game_user[k].character.update()
            keyboard.row(*abilities)
            bot.send_message(message.chat.id, text, reply_markup=keyboard)

            if game_user[k].character.hp <= 0:
                hero_dies(k, bot, message)
                return 0

            if game_user[k].monster.hp <= 0:
                monster_dies(k, bot, message)
                return 0

            hp_bar = 'Opponents hp: '+'#'*int(game_user[k].monster.hp) + '\n\nYour hp: '+'#'*int(game_user[k].character.hp)
            bot.send_message(message.chat.id, hp_bar)

            return 0

        if game_user[k].character.role == 'warrior':
            if message.text.lower() == 'stun attack: stuns opponent for 1 round':
                stun = game_user[k].character.stun()
                if stun == 'stun':
                    game_user[k].monster.score = 2
                    abilities = game_user[k].character.update()
                    keyboard.row(*abilities)
                    bot.send_message(message.chat.id, 'With blunt strike you stun the opponent. He will miss his next turn.', reply_markup=keyboard)
                    return 0
                else:
                    bot.send_message(message.chat.id, 'Stun attack is currently on a cooldown')
                    return 0

            if message.text.lower() == 'second breath: heals 2-4 hp':
                text = game_user[k].character.second_breath()
                if text != 0:
                    abilities = game_user[k].character.update()
                    keyboard.row(*abilities)
                    bot.send_message(message.chat.id, text, reply_markup=keyboard)
                    return 0
                else:
                    bot.send_message(message.chat.id, 'You have already used second breath')
                    return 0

        if game_user[k].character.role == 'mage':
            if message.text.lower() == 'fireball: deals 3 damage':
                fireball = game_user[k].character.fireball()
                if fireball == 'fireball':
                    game_user[k].monster.hp -= 3

                    text = 'You launch fireball setting opponent on fire. He recieves 3 damage'
                    text = monster_attacks(k, text)
                    abilities = game_user[k].character.update()
                    keyboard.row(*abilities)
                    bot.send_message(message.chat.id, text, reply_markup=keyboard)

                    if game_user[k].character.hp <= 0:
                        hero_dies(k, bot, message)
                        return 0

                    if game_user[k].monster.hp <= 0:
                        monster_dies(k, bot, message)
                        return 0 

                    return 0
                else:
                    bot.send_message(message.chat.id, 'Fireball is currently on a cooldown')
                    return 0

            if message.text.lower() == 'healing spell: heals 2-3 hp':
                text = game_user[k].character.healing()
                if text != 0:
                    abilities = game_user[k].character.update()
                    keyboard.row(*abilities)
                    bot.send_message(message.chat.id, text, reply_markup=keyboard)
                    return 0
                else:
                    bot.send_message(message.chat.id, 'You have already used healing spell')
                    return 0

        if (message.text.lower() in ['attack', 'healing spell: heals 2-3 hp', 'fireball: deals 3 damage', 'stun attack: stuns opponent for 1 round', 'second breath: heals 2-4 hp']) == False:
            bot.send_message(message.chat.id, 'Use options available on the buttons')
            return 0




def monster_dies(k, bot, message):
    global game_user

    game_user[k].is_fighting = False
    game_user[k].character.score += 5
    game_user[k].monster.score = 0
    text = 'Your final hit finishes off '+game_user[k].monster.race+'. You walk victoriously away from the battle.'

    moves = game_user[k].determine_possible_moves()
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row(*moves)
    keyboard.row('Look around', 'Search', 'Inventory')

    game_folder.generate_dungeon.draw_dungeon(game_user[k].dungeon, [game_user[k].x, game_user[k].y], k, 
                                                folder='game_folder/', 
                                                map_found=game_user[k].has_map)
    file_name = 'game_folder/dungeon_map_'+str(k)+'.png'
    bot.send_photo(message.chat.id, photo=open(file_name, 'rb'))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    return 0


def hero_dies(k, bot, message):
    global game_user

    game_user[k].dead = True
    game_user[k].character.delete_character(message.from_user.id, folder='game_folder/')
    text = 'The final hit was too much for your feeble body. Your legs don\'t support you anymore, you fall down on the ground and die.\n'
    text += 'Another life that won\'t be remembered...'
    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, 'GAME OVER')
    return 0


def monster_attacks(k, text):
    global game_user

    if game_user[k].monster.score == 3 or game_user[k].monster.score == 2: # stunned
        game_user[k].monster.score -= 1
    else:
        dmg = numpy.random.randint(low=1, high=3)
        text += '\n'

        if game_user[k].monster.role == 'warrior':
            roll_to_hit = roll(game_user[k].monster.strength)
            if roll_to_hit == 0:
                dmg = 3 #critical hit
                text += 'Opponent deals a critical hit! '
            if roll_to_hit < 3:
                text += game_user[k].monster.race+' blows a series of hits and deals '+str(dmg)+' damage to you.'
                game_user[k].character.hp -= dmg
            else:
                text += 'Opponent misses!'

        if game_user[k].monster.role == 'mage':
            roll_to_hit = roll(game_user[k].monster.intellect)
            if roll_to_hit == 0:
                dmg = 3 #critical hit
                text += 'Opponent deals a critical hit! '
            if roll_to_hit < 3:
                text += 'Using arcane powers '+game_user[k].monster.race+' deals '+str(dmg)+' damage to you.'
                game_user[k].character.hp -= dmg
            else:
                text += 'Opponent misses!'

    return text


def open_inventory(k, bot, message):
    global game_user

    inventory = game_user[k].character.show_inventory()
    if game_user[k].complete == False: 
        inventory += ['Close']
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    for i in range(len(inventory)):
        item = str(inventory[i])
        keyboard.row(item)
    text = game_user[k].character.name + '\'s inventory:' 
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    return 0


def end_game(k, bot, message):
    global game_user

    game_user[k].character.save_character(message.from_user.id, folder='game_folder/')

    if game_user[k].how_many_rooms_left() == 0: 
        likes = numpy.random.randint(low=11, high=15)
    else: 
        likes = numpy.random.randint(low=8, high=12) 
    place = ratings(message, game_user[k].character.score, game_user[k].character.name, likes)
    if place == 1: add = 'st'
    if place == 2: add = 'nd'
    if place == 3: add = 'rd'
    if place > 3: add = 'th'
    text = game_user[k].character.name+', powerful '+game_user[k].character.role+', overcame all obstacles, '+ \
    'defeated all monster, reached final destination and now can peacefully retire. \nYour final score is: '+str(game_user[k].character.score)+\
    '.\nYou are on '+str(place)+add +' place in global ranking!\n\nTo see the whole ranking type /rating_game.\nTo start new game type /game.'
    bot.send_message(message.chat.id, text)
    return 1


def roll(hero_stat):
    dice = numpy.random.randint(low=1, high=101, size=1)
    # 2 = regular success; 1 = hard success; 0 = extreme success; 3 = fail
    if dice <= hero_stat: 
        if dice <= int(hero_stat/5):
            return 0
        elif dice <= int(hero_stat/2):
            return 1
        else:
            return 2
    else: 
        return 3



def ratings(message, new_score, character_name, new_likes):
    if len(character_name) > 30:
        character_name = character_name[:30]

    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()

    user_name = message.from_user.first_name
    user_id = message.from_user.id
    c.execute('SELECT * FROM rating WHERE user_id=?', [(user_id)])
    scores = c.fetchall()
    scores = numpy.asarray(scores)
    if len(scores) == 1:
        scores = scores[0]
        if new_score > int(scores[1]):
            c.execute('INSERT or REPLACE INTO rating VALUES (?,?,?,?,?)', 
                (scores[0], int(new_score), character_name, int(scores[3])+new_likes, user_id))
            conn.commit()
        
    elif len(scores) == 0:
        c.execute('INSERT INTO rating VALUES (?,?,?,?,?)', 
                (user_name, int(new_score), character_name, new_likes, user_id))
        conn.commit()
    else:
        logging.warning('There is someone else with the same user id')



    c.execute('SELECT * FROM rating')
    players = c.fetchall()
    conn.close()

    score = numpy.zeros(len(players))
    likes = numpy.zeros(len(players))
    for i in range(len(players)):
        score[i] = players[i][1]
        likes[i] = players[i][3] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(score))
    players = players[index][:10]
    score = score[index][:10]
    likes = likes[index][:10]

    for i in range(len(score)):
        if i != 0 and score[i] == score[i-1]:
            continue

        sel = (score == score[i])
        temp2 = likes[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]

    k, = numpy.where(players[:,0] == user_name)
    
    conn.close()
    return k[0]+1


def show_rating(bot, message):
    fig, ax = plt.subplots(1, frameon=False, figsize=(6,4)) 
    ax.xaxis.set_visible(False) 
    ax.yaxis.set_visible(False) 
    
    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM rating')
    players = c.fetchall()
    conn.close()

    score = numpy.zeros(len(players))
    likes = numpy.zeros(len(players))
    for i in range(len(players)):
        score[i] = players[i][1]
        likes[i] = players[i][3] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(score))
    players = players[index][:10]
    score = score[index][:10]
    likes = likes[index][:10]

    for i in range(len(score)):
        if i != 0 and score[i] == score[i-1]:
            continue

        sel = (score == score[i])
        temp2 = likes[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]

    columns = ['Name', 'Score', 'Character', 'Likes']
    index = range(1, len(players)+1, 1)
    dataframe = pandas.DataFrame(data=players[:,0:4], index=index, columns=columns)

    table_obj = table(ax, dataframe, loc='center', colWidths=[0.1, 0.1, 0.1, 0.1])  
    table_obj.auto_set_font_size(False)
    table_obj.set_fontsize(10)
    plt.tight_layout(rect=(-0.6, -0.3, 1.6, 1.3))
    plt.savefig('game_folder/score.png', dpi=150)
    plt.close(fig)

    with open('game_folder/score.png', 'rb') as result:
        bot.send_photo(message.chat.id, result)
        result.close()


def add_likes(k, bot, message, sender_id, sender_chat_id, new_likes):
    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()

    c.execute('SELECT * FROM rating WHERE user_id=?', [(sender_id)])
    scores = c.fetchall()
    scores = numpy.asarray(scores)
    if len(scores) == 1:
        scores = scores[0]
        c.execute('INSERT or REPLACE INTO rating VALUES (?,?,?,?,?)', 
            (scores[0], int(scores[1]), scores[2], int(scores[3])+new_likes, sender_id))
        conn.commit()
    else:
        logging.warning('There is someone else with the same user id')
    conn.close()


    bot.send_message(sender_chat_id, 'You recieved '+u'\U0001F44D'+' from '+message.from_user.first_name)

    user_name = message.from_user.first_name
    user_id = message.from_user.id
