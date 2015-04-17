from twitterbot.twitter_bot import get_mongo


def add_data(mongo, key, data):
    mongo[key].insert_many(data)

mongo = get_mongo()

mongo.sentences.remove()
mongo.words.remove()
mongo.since_id.drop()

sentences = [{'type': 'adjective', 'sentence': 'I really appreciate how {} you are.'},
             {'type': 'adjective', 'sentence': 'I am so impressed by how {} you are.'},
             {'type': 'noun', 'sentence': 'Your {} is a great inspiration.'},
             {'type': None,
              'sentence': 'You are such a bright light and I am so glad you are here with me.'},
             {'type': None, 'sentence': 'My world is a better place with you in it.'},
             {'type': None, 'sentence': 'Your contributions bring great value.'},
             {'type': None, 'sentence': 'I keep finding new wonderful things about you!'}]
add_data(mongo, 'sentences', sentences)

words = [{'type': 'adjective', 'word': 'smart'},
         {'type': 'adjective', 'word': 'helpful'},
         {'type': 'adjective', 'word': 'kind'},
         {'type': 'adjective', 'word': 'hard-working'},
         {'type': 'adjective', 'word': 'meticulous'},
         {'type': 'adjective', 'word': 'diligent'},
         {'type': 'adjective', 'word': 'courageous'},
         {'type': 'noun', 'word': 'intelligence'},
         {'type': 'noun', 'word': 'kindness'},
         {'type': 'noun', 'word': 'diligence'},
         {'type': 'noun', 'word': 'courage'}]
add_data(mongo, 'words', words)
