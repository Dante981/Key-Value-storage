import asyncio
import sys,os
import random

import Client

cl_l = []

async def test_clien():

    k1 = random.randint(0,99999)
    k2 = random.randint(0,99999)
    k3 = random.randint(0,99999)
    k4 = 's'*random.randint(5,99)
    
    await asyncio.sleep(random.randint(2,60))
    cl = Client.Client()
    await asyncio.sleep(random.randint(1,10))
    cl.set(k1,random.randint(0,99999))
    await asyncio.sleep(random.randint(1,10))
    cl.delete(k1)
    await asyncio.sleep(random.randint(1,10))
    cl.mset(k2,[random.randint(0,99999) for x in range(10)],k3,[[[[[[[[]]]]]]]])
    await asyncio.sleep(random.randint(1,10))
    cl.set(k4,{2:3})
    await asyncio.sleep(random.randint(1,10))
    cl.get(k3)
    await asyncio.sleep(random.randint(1,10))
    cl.mget(k2,k3,k4)


async def clients():
    client1_task = asyncio.create_task(test_clien())
    client2_task = asyncio.create_task(test_clien())

async def main():
    for i in range(1000):
        cl_l.append(asyncio.create_task(test_clien()))

    await cl_l[len(cl_l)-1]

if __name__ == "__main__":
    asyncio.run(main())
    