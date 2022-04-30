CC = gcc
CFLAGS = -Wall -g

all: testbench.out

testbench.out: test.o matrix.o layer.o
	$(CC) $(CFLAGS) test.o matrix.o layer.o -o testbench.out

test.o: test.c
	$(CC) $(CFLAGS) -c test.c -o test.o

matrix.o: matrix.c
	$(CC) $(CFLAGS) -c matrix.c -o matrix.o

layer.o: layer.c
	$(CC) $(CFLAGS) -c layer.c -o layer.o

clean:
	rm *.o *.out
