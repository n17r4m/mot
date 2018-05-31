"""
Compare io_throughput for COPY TO vs regular driver
"""

import config

import numpy as np

import traceback

from uuid import uuid4, UUID

from lib.Database import Database

from time import time


async def main(args):
    await test(int(args[0]))


def particleFilter(p):
    if p["area"] < 100:
        return True
    if p["area"] > 2000:
        return True


async def test(N):
    db = Database()

    inserts = np.random.randint(0, 30000, (N, 5))

    # await db.vacuum()
    # try:
    #     print("Method 1: vanilla inserts")
    #     start = time()

    #     await db.executemany("""
    #             INSERT INTO io_test (col1, col2, col3, col4, col5)
    #             VALUES ($1, $2, $3, $4, $5)
    #             """, list(inserts))

    #     print("Inserting "+str(N)+" records took "+str(time()-start))

    # except Exception as e:
    #     print(e)
    #     traceback.print_exc()

    # # await db.vacuum()
    # try:
    #     print("Method 2: vanilla transaction inserts")
    #     start = time()
    #     tx, transaction = await db.transaction()

    #     await tx.executemany("""
    #             INSERT INTO io_test (col1, col2, col3, col4, col5)
    #             VALUES ($1, $2, $3, $4, $5)
    #             """, list(inserts))

    #     await transaction.commit()
    #     print("Inserting "+str(N)+" records took "+str(time()-start))

    # except Exception as e:
    #     print(e)
    #     traceback.print_exc()
    #     await transaction.rollback()

    # await db.vacuum()
    try:
        print("Method 3: copy-to")
        start = time()
        # np.savetxt('/home/mot/tmp/io_test.csv', inserts, delimiter=',', fmt='%d')

        with open("/home/mot/tmp/io_test.csv", "w") as f:
            f.write("col1, col2, col3, col4\n")
            for row in inserts:
                f.write("{},{},{},{}\n".format(row[0], row[1], row[2], row[3]))

        tx, transaction = await db.transaction()
        await tx.execute(
            """
            COPY io_test (col1, col2, col3, col4) FROM '/home/mot/tmp/io_test.csv' DELIMITER ',' CSV HEADER;
            """
        )

        await transaction.commit()
        print("Inserting " + str(N) + " records took " + str(time() - start))

    except Exception as e:
        print(e)
        traceback.print_exc()
        await transaction.rollback()
