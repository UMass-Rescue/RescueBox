#### Server Process Usage:

Find the PID of the process running on port 5000 using lsof -i :5000 -t.
Use ps -p $SERVER_PID to get the CPU and memory usage of that specific process.

#### Disk Usage:

Track disk I/O with iostat -d 1 2.

#### Network Usage:

Shows network statistics for the specific port (5000), using netstat -an and netstat -ib for interface stats.
Also tracks incoming/outgoing packets related to the process using netstat -ib.

#### System Info:

Provides general system information like uptime, CPU, and memory.
