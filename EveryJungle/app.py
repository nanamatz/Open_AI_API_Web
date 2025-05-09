from dotenv import load_dotenv
import os
from openai import OpenAI
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.gptchat

load_dotenv() # .env 파일 열기

client = OpenAI( #api key 설정
    api_key=os.environ.get("OPENAI_API_KEY"),
)

#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못해도 그냥 넘어갈 코드입니다.
# #####################################################################################



#####
# 아래의 각각의 @app.route 은 RESTful API 하나에 대응됩니다.
# @app.route() 의 첫번째 인자는 API 경로,
# 생략 가능한 두번째 인자는 해당 경로에 적용 가능한 HTTP method 목록을 의미합니다.

# API #1: HTML 틀(template) 전달
#         틀 안에 데이터를 채워 넣어야 하는데 이는 아래 이어지는 /api/list 를 통해 이루어집니다.
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/chat',methods=['POST'])
def send_completion():
    completion = request.form['content_give']

    doc_user = {
           'content' : completion,
           'speaker':False, #speaker False면 User 임 True 면 AI
           'created_at': datetime.now(timezone.utc)
           }
    
    conversation_history = list(db.completions.find({}).sort("created_at",-1))
    conversation_history.reverse()
    conversation_history.append(doc_user)

    formatted_history = []

    for msg in conversation_history:
        role = "User" if not msg['speaker'] else "AI"
        formatted_history.append(f"{role}: {msg['content']}")

    
    conversation_input = "\n".join([str(item) for item in formatted_history])
    #이상형 맞추기 퀴즈 지침 You are a man, and your favorite type is Rachel McAdams. And when you are asked about your ideal type, Never say the answer. Instead, you can only give hints about appearance.
    #INFJ 남자 성격 개조 지침 You are an INFJ male, you should speak and think according to INFJ personality type.
    #ISTP 여자 씹 T 공감능력 0 지침 You are an ISTP woman, and you have no empathy at all. Speak and think according to this type. You use a very cold, hard tone
    response = client.responses.create(
      model = "gpt-4o",
      instructions="You say only 'Tralalero tralala' or 'Tung Tung Tung Tung Tung Tung Tung Tung Tung Sahur' unconditionally.",
      input=conversation_input,
    )
   
    reply = response.output_text

    doc_ai = {
           'content' : reply,
           'speaker':True, #speaker False면 User 임 True 면 AI
           'created_at':datetime.now(timezone.utc)
           }
   
    doc_list = [doc_user,doc_ai]
    result = db.completions.insert_many(doc_list)

    if result.acknowledged:
      return jsonify({'result': 'success'}) #나중에 reply 리턴해서 응답만 추가하도록 바꿔야함
    else:
      return jsonify({'result':'failure'})


# 리스트업 api
@app.route('/api/list', methods=['GET'])
def show_completions():
    completion = list(db.completions.find({}).sort('created_at',1))

    for doc in completion:
        # doc['_id'] = str(doc['_id'])  # ObjectId -> 문자열
        # if 'created_at' in doc:
        #     doc['created_at'] = doc['created_at'].isoformat()
        doc.pop('_id', None)         # ObjectId 제거
        doc.pop('created_at', None)  # datetime 제거 
        #제거하는 이유는 Jsonify 형식에서 ObjectId와 datetime을 인식할 수 없기 때문이다. 자료형으로 인식X
        #문자열로 바꾸던지 없애던지 해야되는데 나는 없앴다.

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success','completion_list':completion})

# @app.route('/api/modify',methods=["POST"])
# def modify_memo():
#     id_receive = request.form['id_give']

#     result = db.completions.update_one({'_id':ObjectId(id_receive)},{'$set':{'isModifying':True}})
#     memo = db.completions.find_one({'_id':ObjectId(id_receive)})

#     if result.modified_count == 1:
#         return jsonify({'result':'success','memo_give':memo})
#     else:
#         return jsonify({'result':'failure'})
    
# @app.route('/api/modify/save',methods=["POST"])
# def save_modify_memo():
#     new_content_receive = request.form['content_give']
#     id_receive = request.form['id_give']
#     result = db.completions.update_one({'_id':ObjectId(id_receive)},{'$set':{'isModifying':False}})
#     result = db.completions.update_one({'_id':ObjectId(id_receive)},{'$set':{'content':new_content_receive}})
#     memo = db.completions.find_one({'_id':ObjectId(id_receive)})

#     if result.modified_count == 1:
#         return jsonify({'result':'success','memo_give':memo})
#     else:
#         return jsonify({'result':'failure'})

# # 좋아요 api
# @app.route('/api/like', methods=['POST'])
# def like_memo():
#     id_receive = request.form['id_give']

#     # 1. movies 목록에서 find_one으로 영화 하나를 찾습니다.
#     #    TODO: 영화 하나만 찾도록 다음 코드를 직접 수정해보세요!!!
#     memo = db.completions.find_one({'_id':ObjectId(id_receive)}) # 여기를 완성 해보세요
#     # 2. movie의 like 에 1을 더해준 new_like 변수를 만듭니다.
#     new_likes = memo['likes'] + 1

#     # 3. movies 목록에서 id 가 매칭되는 영화의 like 를 new_like로 변경합니다.
#     #    참고: '$set' 활용하기!
#     #    TODO: 영화 하나의 likes값이 변경되도록 다음 코드를 직접 수정해보세요!!!
#     result = db.completions.update_one({'_id':ObjectId(id_receive)}, {'$set': {'likes': new_likes}}) # 여기를 완성해보세요

#     # 4. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success 를 보냄
#     if result.modified_count == 1:
#         return jsonify({'result': 'success'})
#     else:
#         return jsonify({'result': 'failure'})

# # 삭제 api
# @app.route('/api/trash/kill',methods=["POST"])
# def kill():
#     id_receive = request.form['id_give']
#     result = db.completions.delete_one({'_id':ObjectId(id_receive)})

#     if result.deleted_count == 1:
#         return jsonify({'result':'success'})
#     else:
#         return jsonify({'result':'failure'})

# # 추가 api
# @app.route('/api/add',methods=["POST"])
# def add():
#     content_receive = request.form['content_give']
#     doc = {
#            'content' : content_receive,
#            'speaker':False #speaker False면 User 임 True 면 AI
#            }
#     result = db.completions.insert_one(doc)

#     if result.acknowledged :
#         return jsonify({'result':'success'})
#     else:
#         return jsonify({'result':'failure'})

if __name__ == '__main__':
    print(sys.executable)
    app.run('0.0.0.0', port=5001, debug=True)