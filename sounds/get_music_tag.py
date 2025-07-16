from tinytag import TinyTag
import eyed3 
import pprint 

tag = TinyTag.get('/Users/alirezadirafzoon/Baha_Awakening_(Michael_Brun_Mix).mp3')
# pprint.pprint(dir(tag))
fields = [k for k in dir(tag) if k[0] != '_']
print(fields)










# af = eyed3.load('/Users/alirezadirafzoon/Baha_Awakening_(Michael_Brun_Mix).mp3')
# print
