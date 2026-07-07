install rescuebox procedure on a mac:

1 save attached script to a file named rb.sh

	Hover your mouse over the file in the Slack message.
	Select Download.

2 open a Terminal and run this rb.sh script

  Press Command (⌘) + Spacebar at the same time to open Spotlight Search.
  Type Terminal and press Enter. 
  or Launchpad -> termimal .
  
  mv ~/Downloads/rb.sh .
  chmod +x rb.sh
  ./rb.sh 2>&1 | tee rb.log
  
3 the script does a lot of package installer "brew" steps , it will take some time,

 if its all good in the end it will start the rescuebox app
 
 if there are errors then we need to look into rb.log and root-cause -> fix and continue

4 orbStack issue ,this cmd on line 47 
   brew install --cask orbstack
sometimes fails . try running this cmdline in terminal and then run
   open -g -a OrbStack
if this opens a UI accept and close. re run the rb.sh script to continue..
 
