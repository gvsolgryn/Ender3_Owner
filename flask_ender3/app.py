from flask import Flask, render_template, json, request, redirect, url_for
from flask_mqtt import Mqtt
from flask_socketio import SocketIO

import time

from module import idpw, dbModule

import ast

app = Flask(__name__, static_folder='./ender3_static')
app.config['SECRET'] = 'mqttSocketIO'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = idpw.mqtt_host
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = idpw.mqtt_id
app.config['MQTT_PASSWORD'] = idpw.mqtt_pw
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins="*")
db = dbModule.Database()

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('conn')
def handle_conn(data):
    print(data['data'])
    sql = 'SELECT status FROM psu WHERE id = 1'
    db_data = db.executeOne(sql)
    print(db_data['status'])
    socketio.emit('psu_status', db_data['status'])
    

@socketio.on('subscribe')
def handle_subscribe():
    mqtt.subscribe('octoPrint/temp/#')
    print('노즐 및 배드 온도 센서 구독 완료')


@socketio.on('unsubscribe_all')
def handle_unsubscribe_all():
    mqtt.unsubscribe_all()  
    print('전체 구독 해제 완료')


@socketio.on('y_up')
def xy_up(val):
    mqtt.publish('printer/control/y/' + str(val), str(val))
    print('Y 축 ' + val + '만큼 위로 이동 완료')


@socketio.on('x_left')
def xy_left(val):
    mqtt.publish('printer/control/-x/' + str(val), str(val))
    print('X 축 ' + val + '만큼 왼쪽으로 이동 완료')


@socketio.on('xy_home')
def xy_home():
    mqtt.publish('printer/control/xy/home', 'xy_Home')
    print('X,Y 축 0, 0 좌표로 이동(Home)')


@socketio.on('x_right')
def xy_right(val):
    mqtt.publish('printer/control/x/' + str(val), str(val))
    print('X 축 ' + val + '만큼 오른쪽으로 이동 완료')


@socketio.on('y_down')
def xy_down(val):
    mqtt.publish('printer/control/-y/' + str(val), str(val))
    print('Y 축 ' + val + '만큼 아래로 이동 완료')


@socketio.on('z_up')
def xy_down(val):
    mqtt.publish('printer/control/z/' + str(val), str(val))
    print('Z 축 ' + val + '만큼 위로 이동 완료')


@socketio.on('z_home')
def xy_down():
    mqtt.publish('printer/control/z/home', 'z_Home')
    print('Z 축 0 으로 이동(Home)')


@socketio.on('z_down')
def xy_down(val):
    mqtt.publish('printer/control/-z/' + str(val), str(val))
    print('Z 축 ' + val + '만큼 아래로 이동 완료')


@socketio.on('printer_on')
def printer_on():
    socketio.emit('usb_on')
    time.sleep(6)
    mqtt.publish('printer/usb/connect', 'connect')
    time.sleep(6)
    mqtt.publish('printer/power/on', 'on')
    print('프린터 전원 On')
    socketio.emit('usb_off')
    mqtt.publish('printer/usb/disconnect', 'disconnect')
    time.sleep(0.5)
    socketio.emit('usb_on')
    time.sleep(5)
    mqtt.publish('printer/usb/connect', 'connect')
    sql = 'UPDATE psu SET status = 1 WHERE id = 1'
    db.execute(sql)
    db.commit()


@socketio.on('printer_off')
def printer_off():
    mqtt.publish('printer/power/off', 'off')
    print('프린터 전원 Off')
    sql = 'UPDATE psu SET status = 0 WHERE id = 1'
    db.execute(sql)
    db.commit()
    time.sleep(0.5)
    socketio.emit('usb_off')
    mqtt.publish('printer/usb/disconnect', 'disconnect')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    ast_payload = ast.literal_eval(data['payload'])
    socketio.emit('mqtt_message', (data, ast_payload))


if __name__ == '__main__':
    #app.run(debug=True, port=3333, ssl_context=('/etc/letsencrypt/live/gvsolgryn.ddns.net/cert.pem', '/etc/letsencrypt/live/gvsolgryn.ddns.net/privkey.pem'))
    socketio.run(app, host='0.0.0.0', port=3333, debug=True, ssl_context=('/etc/letsencrypt/live/gvsolgryn.ddns.net/cert.pem', '/etc/letsencrypt/live/gvsolgryn.ddns.net/privkey.pem'))