from freppledb.asgi import registerService


@registerService("forecast")
def EditForecast(sckt, message):
    print(message)
    sckt.send(message)
