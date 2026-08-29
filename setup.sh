#!/usr/bin/env bash
GREEN='\033[0;32m'
NC='\033[0m'   # No Color / reset
RED='\033[0;31m'
YELLOW='\033[0;33m'
#verify python is installed
if ! command -v python3 >/dev/null 2>&1; then

  echo -e "${RED}Python is not installed!"
  exit 1
fi   
echo "Python 3 found: $(command -v python3)"
# do x

#check for existing virtual environment
if [ -d "./venv" ]; then
    echo -e "venv exists"
else
    echo -e "${YELLOW}venv does not exist. Creating now...${NC}"
    if ! python3 -m venv ./venv; then
      echo -e "${RED} venv creation failed."
      exit 1
    fi
fi

# activate venv
source ./venv/bin/activate

#verify successful venv activation
if [ -z "$VIRTUAL_ENV" ]; then
  echo -e "${RED}Something went wrong activating the virtual environment"
  exit 1
fi

#check that Selenium is installed
if ./venv/bin/python -m pip show selenium; then
    echo "Selenium is installed. Skipping installation..."
else
    #install if missing
    echo -e "${YELLOW}Selenium is not installed. Installing now...${NC}"
    ./venv/bin/python -m pip install selenium
    if [ $? -ne 0 ]; then
      echo e "${RED}Error installing Selenium!"
      exit 1
    fi
fi

printf "${GREEN}Environment successfully setup. Please run \"source ./venv/bin/activate\" before running python scripts${NC}\n"
