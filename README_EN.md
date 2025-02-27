# OSR-VRChat

[中文版](README.md)

An OSR robot driver that implements motion synchronization between the OSR robot and VRChat.

Special thanks to the [Shocking-VRChat](https://github.com/VRChatNext/Shocking-VRChat) coyote project for setting up the framework!

Test QQ group: 1034983762


## How to Use

### Preparation

1. Ensure that both the penetrator's plug and the receiver's socket **are made based on SPS** (**DPS/TPS not supported** because these two plugins lack the OGB data interface for depth calculation).

2. Connect the OSR2 to the computer, turn on the OSR2 switch, and open the **Chrome** browser to the [Mosa controller](https://trymosa.netlify.app/) webpage. Select "Serial" in the top left corner and choose the corresponding serial port in the pop-up window.

![text](images/com_example.png)

- As shown in the image, remember the serial port name in the red box (usually `COM` + a number). Drag the control axis to ensure the OSR device is working properly. After testing, **close the webpage** to release the serial port.

3. Confirm that OSC data interface is enabled in VRChat and that the model’s attachment function is activated.


### Parameter Settings
`objective`: The action type. The table below lists all allowed values and explanations:

| `objective` | Explanation |
|-------------|-------------|
| `inserting_self` | Insert your own plug into someone else's socket |
| `inserting_others` | Insert your own plug into your own socket (e.g., insert into your hand, typically used for testing) |
| `inserted_ass` | Your socket located at the anus is inserted by someone else |
| `inserted_pussy` | Your socket located at the vagina is inserted by someone else |

Please enter the corresponding value in the settings file based on your usage.

\
`com_port`: The serial port for device connection. Enter the serial port number from the preparation (e.g., `COM5`).

The total movement range of OSR2 is **999** units (same as in Mosa).

`max_position`: Upper limit of movement position, range 0-999.

`min_position`: Lower limit of movement position, range 0-999.

`max_velocity`: Speed limit (units/second), range 0-999.

`updates_per_second`: Number of updates per second, range 0-100.


### Running the Program

1. Download the `osr_vrchat.exe` from the Releases section, run the program, and it will generate a settings file and automatically exit on the first run.
2. Follow the above steps to perform device checks and correctly set the parameters.
3. Run the program again to synchronize with VRChat. If parameters are changed, the program needs to be restarted to take effect.


## Q&A

### 1. What is OSR?

OSR stands for **O**pen-source **S**troker **R**obot. Currently, this project only supports OSR2/2+, the most portable and compact model in the OSR lineup, supporting motion on 2/3 axes. Future updates will gradually include support for OSR6 and other more complex robots. For more information, refer to [this webpage](https://discuss.eroscripts.com/t/guide-what-is-the-osr2-sr6-ssr1-and-how-do-i-get-one/158805).

### 2. How to Obtain OSR2 Devices?

Many sellers online offer finished devices and mounts. Prices usually depend on the quality/torque of the servo and the included accessories. You can purchase based on your needs and budget. If you want to build the OSR2 system yourself, refer to [this project](https://www.patreon.com/tempestvr).

### 3. What is OGB?

The full name of the [OGB](https://osc.toys/) project is "Osc Goes Brrr", which synchronizes actions in games with toys that support [Intiface](https://intiface.com/). The author of OGB, Senky, is also the author of the SPS system, which reserved a series of OSC data interfaces at `/avatar/parameters/OGB/*` in the SPS plugin, greatly facilitating depth calculation.


## Update Plan
A wearable solution will be released in March, supporting various positions. Stay tuned.
