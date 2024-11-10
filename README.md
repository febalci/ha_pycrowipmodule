# Home Assistant Crow IP Module Custom Component

This is a custom component for Crow Runner / Arrowhead AAP 8/16 Home Alarm System IP Module Integration to Home Assistant.

see [HA community thread][ha_community_thread] for details

## Requirements:
- Hardware either of thoose are reported working
  - Crow Runner 8/16 with IP Module
  - AAP Elite ESL-2 with ESL-2 APP POD
- Firmware for Ip Module or APP POD
  - `Ver 2.10.3628 2017 Oct 20 09:48:43`
  Contact AAP Support to request exact Firmware version [email](mailto:tech@aap.co.nz)

## Installation using HACS

Follow steps described [here][hacs_custom_repository] to add [this repository][repo_root] as custom integration

Repository: https://github.com/febalci/ha_pycrowipmodule

Type: Integration

You should see this after adding the repository

![hacs_custom]



## Manual Installation

You will need to install the crowipmodule manually.

### Setup
- create custom_components folder if it does not exist to get following structure\
  `config/custom_components`

#### Manual file copy
- create crowipmodule folder inside custom_components folder\
  `config/custom_components/crowipmodule`
- copy all files from [custom_components/crowipmodule/](custom_components/crowipmodule/) into the previously created folder

#### Cloning repo
- use Terminal AddOn or ssh to connect to HomeAssistant
- checkout ha_pycrowipmodule into config directory\
  `git clone https://github.com/febalci/ha_pycrowipmodule`
- cd into config/custom_components folder\
  `cd config/custom_components`
- create symlink for crowipmodule\
  `ln -s ../ha_pycrowipmodule/custom_components/crowipmodule crowipmodule`

### Restart HomeAssistant

### Configuration

you can use the [sample configuration](sample_configuration.yaml) as a starting point

### Restart HomeAssistant

## Configuration Details
```
crowipmodule:
  host: xxx.xxx.xxx.xxx ( any IP adress it is recommanted to set a static IP adress)
  port: 5002
  keepalive_interval: 60
  timeout: 20
  areas:
    1:
      name: 'Home'              (Name it like you want)
      code: '1234'              (Keypad Arm and Disarm Code (User code))
      code_arm_required: False  (is code required to arm area, Optional defaults to True)
    2:
      name: 'None'              (Name it like you want)
      code: '1234'              (Keypad Arm and Disarm Code (User code))
      code_arm_required: False  (is code required to arm area, Optional defaults to True)
  outputs:
    3:
      name: 'Main Router'       (Name it like you want)
    4:
      name: 'USV Restart'       (Name it like you want)
  zones:
    1: --> depends on how many zones your installation has. 8/16 zone entries
      name: 'Entrance'          (Name it like you want)
      type: 'motion'            (supported types are motion, door, window)
    2:
      ...
```

[repo_root]: https://github.com/febalci/ha_pycrowipmodule
[ha_community_thread]: https://community.home-assistant.io/t/custom-component-crow-runner-arrowhead-aap-8-16-alarm-ip-module/130588/23
[hacs_custom_repository]: https://hacs.xyz/docs/faq/custom_repositories/
[hacs_custom]: hacs_custom.png
