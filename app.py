from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect
import MySQLdb       
import math
import time
import configparser as ConfigParser
import random
import serial
async_mode = None
app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 


def background_thread(args):
    count = 0  
    dataList = []  
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    ser = serial.Serial('/dev/ttyACM0')
    
    while True:
        if args:
          dbV = dict(args).get('db_value')
        else:
          dbV = ''  
         
        socketio.sleep(1)
  
        values = ser.readline().decode().strip()
        values = values.split(',')
        
        if dbV == 'start':
          if count == 0:
            print('adasda')
            socketio.emit('my_response',{'temperature':'START','humidity':'','light':'','count':''},namespace='/test')
            
          count += 1
              
          dataObject = {"temperature":values[0],"humidity":values[1],"light":values[2]}
          dataList.append(dataObject)
          socketio.emit('my_response', {'temperature':values[0],'humidity':values[1],'light':values[2],'count':count},namespace='/test')
          
        else:
          
          if len(dataList)>0:
              print('-----------stop------')
              dataObjToStr = str(dataList).replace(",","\"");
              cursor = db.cursor()
              cursor.execute("INSERT INTO senzors (hodnoty) VALUES (%s)",(dataObjToStr,))
              
              db.commit()
              dataList = []
              count = 0
              socketio.emit('my_response', {'temperature':'STOP','humidity':'','light':'','count':''},namespace='/test')

          
    db.close()

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    return render_template('graph.html', async_mode=socketio.async_mode)
    
@app.route('/db')
def db():
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  cursor.execute('''SELECT  hodnoty FROM  graph WHERE id=1''')
  rv = cursor.fetchall()
  return str(rv)    

@app.route('/dbdata/<string:num>', methods=['GET', 'POST'])
def dbdata(num):
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  print(num)
  cursor.execute("SELECT hodnoty FROM  graph WHERE id=%s", num)
  rv = cursor.fetchone()
  return str(rv[0])
    
@socketio.on('my_event', namespace='/test')
def test_message():   
    emit('my_response',
         {'temperature':'START','humidity':'','light':'','count':''})

@socketio.on('db_event', namespace='/test')
def db_message(message):   
    session['db_value'] = message['value']    


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    emit('my_response',
         {'temperature': 'Disconnected!','humidity':'','light':'', 'count': ''})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
   # emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=81, debug=True)
