from freppledb.asgi import registerService

print("ppppp")


@registerService("forecast")
def EditForecast(sckt, message):
    print(message)
    sckt.send(message)
