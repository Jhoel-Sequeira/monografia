from flask import Flask, request, render_template
from flask_mail import Mail, Message



def enviar_correo(app,title, recipient, accion, dia , mes , hora):
    enviar = "veterinariabuenproductor@gmail.com"
    app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = enviar,
    MAIL_PASSWORD = 'zildwettliojgcnk')
    mail = Mail(app)

    msg = Message(
        subject=title,
        sender=enviar,
        recipients=[recipient]
    )
    msg.html = render_template('sistema/correo.html',accion = accion,dia = dia,mes = mes,hora = hora )
    mail.send(msg)