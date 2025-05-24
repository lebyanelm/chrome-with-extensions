#!/bin/bash

# Start Selenium in background (using supervisord)
/opt/bin/entry_point.sh &

until curl -s http://localhost:4444/wd/hub/status | grep -q '"ready": true'; do
  echo "Waiting for Selenium WebDriver..."
  sleep 2
done

# Now run your script
echo "Selenium is ready. Running your script..."
python3 /home/seluser/token-manager/__manager__.py