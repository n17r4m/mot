
import numpy as np
import time

# Step 0 (importing the library)
# from numap import NuMap, imports
# from papy.core import Worker, Piper, Plumber
from lib.Database import Database

async def main(args):
    
    db = Database()
    tx, transaction = await db.transaction()
     
     
     
     
    q1 = "create table x (id serial primary key, key integer, val text)"
    s1 = "table created {time}"
    q2 = "insert into x (key,val) values (generate_series(1,20000000), to_char(trunc(random()*1000000),'999999'))"
    s2 = "rows inserted {time}"
    q3 = "select * from x limit 10"
    s3 = "select {time}"
    s4 = "commit {time}"
    q4 = "drop table x"
    
    start = time.time()
    await tx.execute(q1)
    print(s1.format(time=time.time()-start))
    
    start = time.time()
    await tx.execute(q2)
    print(s2.format(time=time.time()-start))
    
    start = time.time()
    await tx.execute(q3)
    print(s3.format(time=time.time()-start))
    
    start = time.time()
    await transaction.commit()
    print(s4.format(time=time.time()-start))
    
