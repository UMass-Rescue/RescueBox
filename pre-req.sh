# this runs inside the container, you open a VScode terminal cd to git repo and run pre-req.sh
cd /home/rbuser
sudo ln -s /home/rbuser/.ollama /root/.ollama
sudo nohup ollama serve > ollama.log 2>&1 &
sudo nohup /usr/sbin/rabbitmq-server > rabbitmq.log 2>&1 &
cd /home/rbuser/RescueBox
nohup  poetry run python -m src.rb-api.rb.api.main > rb_server.log 2>&1 &

# confirm
# ollama list , should show at least one or two pre populated models
# http://localhost:8000 should show up the rescuebox UI