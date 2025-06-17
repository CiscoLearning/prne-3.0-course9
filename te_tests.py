import os
import sys
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

TE_API_TOKEN = os.getenv("TE_API_TOKEN")
TEST_NAME = os.getenv("TEST_NAME")
TARGET = os.getenv("TARGET")

BASE_URL = "https://api.thousandeyes.com/v7"
HEADERS = {
    "Authorization": f"Bearer {TE_API_TOKEN}",
    "Content-Type": "application/json",
}


def get_first_agent_id() -> Optional[int]:
    url = f"{BASE_URL}/agents"
    response = requests.get(url, headers=HEADERS)

    if response.ok:
        agents = response.json().get("agents", [])
        if agents:
            agent = agents[0]
            print(f"[✓] Using agent: {agent['agentName']} (ID: {agent['agentId']})")
            return int(agent["agentId"])
        else:
            print("[!] No agents found in your account.")
    else:
        print(f"[!] Failed to fetch agents: {response.status_code} - {response.text}")
    return None


def find_existing_test_id(test_name: str) -> Optional[int]:
    url = f"{BASE_URL}/tests/http-server"
    response = requests.get(url, headers=HEADERS)

    if response.ok:
        for test in response.json().get("tests", []):
            if test.get("testName") == test_name:
                return int(test["testId"])
    else:
        print(f"[!] Failed to retrieve tests: {response.status_code} - {response.text}")
    return None


def create_test(
    test_name: str, target: str, agent_id: int, interval: int = 3600
) -> Optional[int]:
    payload = {
        "testName": test_name,
        "type": "agent-to-server",
        "url": target,
        "interval": interval,
        "protocol": "ICMP",
        "enabled": True,
        "agents": [{"agentId": agent_id}],
    }

    url = f"{BASE_URL}/tests/http-server"
    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code == 201:
        test_id = response.json().get("testId")
        print(f"[+] Created test '{test_name}' (ID: {test_id})")
        return int(test_id)
    else:
        print(f"[!] Error creating test: {response.status_code} - {response.text}")
        return None


if __name__ == "__main__":
    print("[*] Starting ThousandEyes test automation...")

    agent_id = get_first_agent_id()
    if agent_id is None:
        sys.exit("[!] No valid agent available. Exiting.")

    test_id = find_existing_test_id(TEST_NAME)
    is_new = False

    if test_id is not None:
        print(f"[✓] Found existing test ID: {test_id}")
    else:
        print(f"[*] No existing test named '{TEST_NAME}' found. Creating a new test...")
        test_id = create_test(TEST_NAME, TARGET, agent_id)
        is_new = True
