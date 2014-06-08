import asyncio

def derp():
    print("DERP!")


@asyncio.coroutine
def greeter(loop):
    asyncio.async(greeter2(loop), loop=loop)
    loop.call_later(1.5, derp)
    while True:
        print("greeter1")
        yield from asyncio.sleep(2, loop=loop)

@asyncio.coroutine
def greeter2(loop):
    for i in range(4):
        print("greeter2", i)
        yield from asyncio.sleep(1,loop=loop)

loop1=asyncio.new_event_loop()
loop2=asyncio.new_event_loop()
loop3=asyncio.new_event_loop()
loop4=asyncio.new_event_loop()

print(loop1,loop2,loop3,loop4)
loop1.run_until_complete(greeter(loop1))