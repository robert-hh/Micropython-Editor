## lcd_io usage

This front-end includes code to allow the pye editor to run on a CircuitPython board with an attached LCD display and accepting text input via UART. This version is called `pye_lcd.py`.  (Note: By using the main pye.py file, you can separately select only LCD display or only UART input by properly selecting the high level Boolean variables: `direct_lcd_io` and `uart_input`.)

This branch relies on the simpleTerminal and editorTerminal class found at [https://github.com/kmatch98/simpleTerminal](https://github.com/kmatch98/simpleTerminal)

To setup the display for your requirements, review and update the `init_display` function as follows:

1. Update the pin connections.  
2. Set up the SPI bus.  
3. Select the correct display library and set the appropriate display settings.

The following sections describes the steps to update the code to match your display requirements:

1. Update the pin connections to match your chip's wiring.

```python
                spi = board.SPI()
                tft_cs = board.D12 # arbitrary, pin not used for my display
                tft_dc = board.D2
                tft_backlight = board.D4
                tft_reset=board.D3
```

This is the meaning of each of these four connections for the SPI bus:

|Pin Name in code |Connection|
|:---|:---| 
|`spi`| `board.SPI()` selects clock, MOSI and MISO for this board
|`tft_cs`|Chip Select|
|`tft.dc`| Data/Command pin|
|`tft_backlight`| Backlight PWM control|
|`tft_reset`| Reset|

2. Set up the SPI bus.  

Edit the `displayio.FourWire` parameters to correspond to the requirements of your display.  For example set the `baudrate`, `polarity`, and `phase` to correspond to the requirements of your display.

```python
                display_bus = displayio.FourWire(
                    spi,
                    command=tft_dc,
                    chip_select=tft_cs,
                    reset=tft_reset,
                    baudrate=24000000,
                    polarity=1,
                    phase=1,
                )
```
***Example:*** In this example, this display uses SPI\_Mode3, requiring `polarity=1` and `phase=1`.  
If using a display requiring SPI_Mode1, then set `polarity=0` and `phase=1`.  More details can be found in this [SPI mode table on Wikipedia] (https://en.wikipedia.org/wiki/Serial_Peripheral_Interface#Mode_numbers).

3. Select the correct display library and set the appropriate display settings.

Select the correct display library and display settings in following lines:

```python
                Editor.xPixels=240 # number of xPixels for the display
                Editor.yPixels=240 # number of yPixels for the display

                Editor.display = ST7789(display_bus, 
                			width=Editor.xPixels, 
                			height=Editor.yPixels, 
                			rotation=0, 
                			rowstart=80, 
                			colstart=0)

```

Edit the `Editor.xPixels=240` and `Editor.yPixels=240` to correspond to the pixel dimensions of your display.

Update the following parameters as required for your display: `rotation=0`, `rowstart=80` and `colstart=0`.


***Example:*** This example shows a 240x240 pixel display using an ST7789 display controller chip.  Because this chip can handle up to 320x240 pixel display, so to accommodate our 240x240 display size, we utilize an 80 pixel offset using the `rowstart` parameter.  Your display library is likely is different than this, and may not require any offset.

## Using UART as an input
Double-check that the settings in the `init_tty` function match your UART hardware connections, especially for `board.TX`, `board.RX` and `baudrate`:

```python
                Editor.uart = busio.UART(board.TX, 
                			board.RX, 
                			baudrate=115200, 
                			timeout=0.1, 
                			receiver_buffer_size=64)
```
