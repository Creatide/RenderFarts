# RenderFarts - Blender Add-on

<p align="center">
  <img src="https://i.imgur.com/SziMKaZ.gif" width="100%" title="RenderFarts Logo">
</p>

### About

What if you could **render images in parts, on multiple computers, stop rendering and then continue** even if you've shut down your beautiful machines? This is something I've longed for a really long time for 3D programs...

**RenderFarts** is a fairly simple Blender addon that splits an image into smaller pieces and renders them to separate files. It sounds self-evident, and it is. But with this simple logic, we can do much of what I mentioned above.

Why it's called **RenderFarts**? The very first prototype was called **RenderParts** but then I farted...

*Remember this add-on is a prototype of the features that I need in my workflow. It could crash and explode but now you've been warned!*

## Features

### Stop and Continue Rendering

<p align="center">
  <img src="https://i.imgur.com/OjVgSkv.gif" width="100%" title="Stop and Continue Rendering">
</p>

This was mainly the reason why I created RenderFarts add-on. It saves tiles to separate files so you just continue from there where you left whenever you want. Just remember to use the exact same file and rendering location and you'll be fine.

### Render With Multiple Computers

<p align="center">
  <img src="https://i.imgur.com/ktHGjhE.gif" width="100%" title="Render Multiple Computers">
</p>

The second best reason for me to use RenderFart is being able to render using multiple computers. I've used some render farms and managers, but many of them are a hassle to set up for simple still images for personal use. For animations and bigger projects, those are all wonderful choices.

Just remember to use the same blend file with the same settings and the same folder location where each of your rendering machines have access. Then you press render and grab a coffee (and/or beer).

### Merge Rendered Image

<p align="center">
  <img src="https://i.imgur.com/7ZWPpVo.gif" width="100%" title="Merge Rendered Images">
</p>

This feature is like butter on bread. Normally you merge images in some 3rd party apps like Photoshop or Gimp but now you can just press the merge button on Render Farts and it will merge pieces for your masterpiece. Just remember that for huge images it can take some time and freeze Blender for a while. 

## Feature Ideas

Here are some feature ideas that could be created to make this addon better. If you're a developer and have got some ninja moves, just fork and be a master Jedi.

[x] Merge rendered parts into the final image inside Blender.

## Installation

 1. Download the [latest release](https://github.com/Creatide/RenderFarts/raw/master/RenderFarts.zip)
 2. In Blender open up *User Preferences > Addons*
 3. Click *Install from File*, select `RenderFarts.zip` and activate the Add-on

## Collaboration & Feedback

On my day to day job, I'm a visual guy, but in my free time, I like to spend some time with code. I'm not super experienced in this area, so all of the bits of advice and improvement suggestions are more than welcome!

If you want to help in creating this add-on better just fork it and create some useful updates. Send me pull requests so I can include your work to official BlenderFart build and give you credit here!

### Contributors

Thank you all for your contributions. **Special thanks to these people for writing code:**

No one here, welcome on board if you make this add-on to better ;)

## License

The MIT License (MIT) Copyright (c) 2020 [Creatide](http://creatide.com) *(*[*Sakari Niittymaa*](http://sakari.niittymaa.com)*)*
