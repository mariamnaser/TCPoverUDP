# Write RDT 3.0 using ABP protocol
# Enviroment
- I am using an MacOS Catelina
- The terminal I am using is zsh
- The IDE I am using is Pycharm

# How to Run in localhost
- Run the proxy server for both sender and receiver using [NEWUDPL](http://www.cs.columbia.edu/~hgs/research/projects/newudpl/newudpl-1.4/newudpl.html)
- Run receiver.py and then sender.py

# Architecture
![architecture](images/architecture.png)

# Course Website Instructions
![1](images/1.png)
![2](images/2.png)
![3](images/3.png)

The original description [pdf](Programming_Assignment_3_%20Implementing_a_Reliable_Transport_Protocol.pdf)

# My test description
My test description is in the [assignment write-up](COMS4119_Assignment4_Programming.pdf)

Basically, I will read from input file [sample.txt](sample.txt) to sender and write the output from the receiver to [output.txt](output.txt) and do diff

```shell script
diff sample.txt output.txt
```

and it will return nothing

# Some useful commands

## Direct connection
First, we can begin with direct connection (without using the proxy server NEWUDPL)
### Receiver command
```sh
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001 > output.txt
```


### Sender command
This is to directly connect to the receiver, not using the newudpl
```sh
python3 sender.py --host localhost --port 5001 --dest_host localhost --dest_port 5000 --timeout 2 < sample.txt
```

## Using NEWUDPL as a proxy server
Now, we use NEWUDPL in the middle

http://www.cs.columbia.edu/~hgs/research/projects/newudpl/newudpl-1.4/newudpl.html

notice that
```shell script
-B bit error rate
Specifies a rate of genarating bit errors for outgoing packets. The rate is in 1/100000(BITERRDENOM).
Available range: 1 - 99999(BITERRDENOM - 1)
Default: 0

-L random packet loss rate
Specifies a rate of genarating random packet loss for outgoing packets. The rate is in percentage.
Available range: 1 - 99
Default: 0

-O out of order rate
Specifies a rate of randomizing oreder of packets. The distination host will receive some packets in out of order in certain rate. The rate is in percentage.
Available range: 1 - 99
Default: 0
```

Sample test:

### The following is out of order test from sender

connect to outbound of receiver
```shell script
./newudpl -vv -p 5001 -i "localhost/*" -o localhost:5003
```

connect to outbound of sender
```shell script
./newudpl -vv -p 5002 -i "localhost/*" -o localhost:5000 -O 80
```

Now the sender argument is
```shell script
python3 sender.py --host localhost --port 5003 --dest_host localhost --dest_port 5002 --timeout 2 < sample.txt
```

Now the receiver argument is 
```shell script
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001
```

do diff check
```shell script
diff sample.txt output.txt
```

### The following is Loss packet test from sender
connect to outbound of receiver
```shell script
./newudpl -vv -p 5001 -i "localhost/*" -o localhost:5003
```

connect to outbound of sender
```shell script
./newudpl -vv -p 5002 -i "localhost/*" -o localhost:5000 -L 60
```

Now the sender argument is
```shell script
python3 sender.py --host localhost --port 5003 --dest_host localhost --dest_port 5002 --timeout 2 < sample.txt
```

Now the receiver argument is 
```shell script
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001
```
do diff check
```shell script
diff sample.txt output.txt
```

### The following is bit error test from sender

connect to outbound of receiver
```shell script
./newudpl -vv -p 5001 -i "localhost/*" -o localhost:5003
```

connect to outbound of sender
```shell script
./newudpl -vv -p 5002 -i "localhost/*" -o localhost:5000 -B 80
```

Now the sender argument is
```shell script
python3 sender.py --host localhost --port 5003 --dest_host localhost --dest_port 5002 --timeout 2
```

Now the receiver argument is 
```shell script
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001
```

do diff check
```shell script
diff sample.txt output.txt
```

### The following is bit error test from receiver
connect to outbound of receiver
```shell script
./newudpl -vv -p 5001 -i "localhost/*" -o localhost:5003 -B 80
```

connect to outbound of sender
```shell script
./newudpl -vv -p 5002 -i "localhost/*" -o localhost:5000
```

Now the sender argument is
```shell script
python3 sender.py --host localhost --port 5003 --dest_host localhost --dest_port 5002 --timeout 2 < sample.txt
```

Now the receiver argument is 
```shell script
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001 > output.txt
```

do diff check
```shell script
diff sample.txt output.txt
```

### The following is packet loss from receiver
connect to outbound of receiver
```shell script
./newudpl -vv -p 5001 -i "localhost/*" -o localhost:5003 -L 60
```

connect to outbound of sender
```shell script
./newudpl -vv -p 5002 -i "localhost/*" -o localhost:5000
```

Now the sender argument is
```shell script
python3 sender.py --host localhost --port 5003 --dest_host localhost --dest_port 5002 --timeout 2 < sample.txt
```

Now the receiver argument is 
```shell script
python3 receiver.py --host localhost --port 5000 --dest_host localhost --dest_port 5001
```

do diff check
```shell script
diff sample.txt output.txt
```


## using natcat
```shell script
nc -vv localhost 5000 -u
```