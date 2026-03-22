# Overview
This is a Home Assistant integration for the pivot monitor HTTP API.

## Development environment setup
1. Set up Home Assistant dev environment as shown in [https://developers.home-assistant.io/docs/development_environment](https://developers.home-assistant.io/docs/development_environment).
1. In the container, add the following folder: `mkdir config/custom_components`.
1. Clone this repo (using access token if you need push access) under that folder:
    ```
    git clone https://ACCESS_TOKEN@github.com/Stickman-Solutions/ha-pivot-integration.git # Write access

    git clone https://github.com/Stickman-Solutions/ha-pivot-integration.git # Read only
    ```