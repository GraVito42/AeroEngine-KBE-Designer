# KNOWLEDGE BASE: PARAPY DOCUMENTATION

This document contains the merged content of the following source files:
- Creating an App - ParaPy Documentation.pdf
- oop_pp_cheatsheet.pdf
- ParaPy Tutorial 3.pdf
- Positioning Cheatsheet.pdf
- proc_oop_cheatsheet - Copy.pdf
- Tutorial 2 ParaPy classes and GUI.pdf
- Tutorial 4.pdf

---



# ========================================================
# START OF SOURCE: Creating an App - ParaPy Documentation.pdf (Category: Parapy Documentation)
# ========================================================

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

## Creating an App 

In this tutorial we will be making a simple ParaPy application. Firstly we will set up a layout of the application containing placeholders. We build a ParaPy model representing a staircase. Then we will build a user interface that allows user to configure the properties of the staircase. 

You will learn 

- Setting up an project 

- Creating a layout for an application 

- Creating a geometric parapy model 

- Integrating a model with the UI 

- Generating and downloading a .step file 

## Idea 

The idea of the app is to create a parametric staircase. The goal of the application to quickly generate a staircase STEP file based on some parameters. Below is an image of the final app we will be making in this tutorial. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

1/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

**==> picture [431 x 299] intentionally omitted <==**

## Approach 

To get started we will first make a rough layout of the application with placeholders which we will fill in later. We will then start making the model of the stairs. The model will contain the rules to generate the geometry of the stairs. We will then connect the model with the UI so that users of the app can edit the properties of the stairs. The changing of the properties will influence the generation of the geometry and the user will see the updated stairs. We finalize the app by adding a option to export the stairs to a .step file. 

## Base app 

In a new python script, we will start by creating our `App` component. The root component that will render the entire application. That component can then be displayed using the `display` function. When the script is executed, a webpage should open displaying ``Hello world'. 

Note that since we are developing an application, we set `reload=True` in the `display` function. When we now make changes to the script, the application will directly be updated. Try it out by changing the text returned in the `render` method. 

 `from parapy.webgui.core import Component, NodeType class App(Component):` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

2/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`def render(self) -> NodeType:`  `return 'Hello world' if __name__ == "__main__": from parapy.webgui.core import display display(App, reload=True)` Reload In the `display` function we set `reload` to `True` . When this is set, the application will reload  whenever it detects changes in the source code. This allows for a nicer development experience. 

The reload function is an experimental feature and might not always work as intended. In these cases a regular application restart is required to see the changes. 

For the remained of this tutorial it is assumed that hot reload is turned on. 

We are now ready to develop our application. 

## App layout 

Let's start by defining the layout of our application. If we look at the app we want to make, we notice 3 main components. 

- The app bar 

- The inputs panel 

- The model viewer 

Now we have to figure out how we divide the available area of the application between these three components. 

The first division we can see is that the page is vertically divided between the app bar and both the inputs panel and the model viewer. Schematically we can draw this division as follows: 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

3/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

**==> picture [431 x 269] intentionally omitted <==**

Now we have a plan for our first step of the layout. That is to split the app into two sections above each other. One being the app bar and the other being the `content` . To achieve this in code we can use the `Split` widget from the `layout` package. This widget allows you to split areas into sections. 

## Layout package 

Make sure that the `layout` package is installed with 

```
pip install parapy-webgui-layout
```

Then the package can be imported using: 

```
fromparapy.webguiimport layout
```

Let's try it out by adding the split widget with some placeholders: 

```
classApp(Component):
defrender(self)-> NodeType:
return layout.Split[
'AppBar',
'content'
]
```

As you can see the desired effect is not quite achieved. By default, the `Split` widget splits the area horizontally. We can specify that the content should be split vertically instead: 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

4/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

 `class App(Component): def render(self) -> NodeType: return layout.Split(orientation='vertical')[ 'AppBar', 'content' ]`  

Now it looks like our changes have the desired effect. However, this is not exactly true. Let's inspect the `Split` to make sure that it is dividing the entire web page for our two sections. We can achieve this by temporarily adding a background color: 

```
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            style={'backgroundColor':'gray'})[
'AppBar',
'content'
]
```

The result is unexpected. We would like the entire webpage to be in our area. However only the two most upper rows are colored. This is caused because a `Split` by default only takes the minimal required height. Since we currently only have two rows of text, the `Split` will only be that tall. We would like for the split to occupy the entire web page. We can do exactly that by providing `height="100%"` to the `Split` . A height of `"100%"` means that the `Split` will be as tall as 100% of the parent. In our case the parent is the entire web page since the `Split` is the first widget we render. 

```
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            height='100%',
                            style={'backgroundColor':'gray'})[
'AppBar',
'content'
]
```

When we apply the above changes, we can see that the split occupies the entire page like we wanted. However, the second text is now in the middle of the page. This is because `Split` divides the available area in sections. By default all sections are equally large. In our case the first section containg the app bar should only be as high as the app bar itself. 

We can achieve this by providing the `weights` of each section. The `weights` controls how the available area is divided between the sections. If `weights=[1, 2]` would be provided to the `Split` , the second section would be twice as large as the first. Additionally we can provide a weight of `0` to a section. This means that the section should be as small as its content allows. This is exactly what we need for the app bar. Thus we want a appbar with weight 0 and the other should be as high as the remainder: 

 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

5/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`class App(Component):`  `def render(self) -> NodeType: return layout.Split(orientation='vertical', height='100%', weights=[0, 1], style={'backgroundColor': 'gray'})[ 'AppBar', 'content' ]`  

Now that we have the desired result we can again remove the background color and add the actual app bar instead of our placeholder. ParaPy provides an `AppBar` which contains some nice build in features to work with the cloud. The widget can be imported using: 

```
fromparapy.webgui.app_barimport AppBar
```

## AppBar 

The AppBar widget is provided by default with the parapy-webgui package. There is no need to install any additional packages. 

We can also provide the appbar with a title to display. 

```
fromparapy.webgui.app_barimport AppBar
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            height='100%',
                            weights=[0,1])[
            AppBar(title="Stairs Configurator"),
'content'
]
```

When we now check the result, we have a nice `AppBar` and a placeholder for the content. Now that we know how a `Split` works we can use the same technique to split the `content` in two sections for the inputs panel and the model viewer. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

6/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

**==> picture [431 x 268] intentionally omitted <==**

In this case we want to split the available area horizontally. The inputs panel should be as small as its content whilst the model viewer should be as big as possible to make use of the real estate. 

```
fromparapy.webgui.app_barimport AppBar
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            height='100%',
                            weights=[0,1])[
            AppBar(title="Stairs Configurator"),
            layout.Split(height='100%',
                         weights=[0,1])[
'inputs panel',
'model viewer'
]
]
```

As the results show, the inputs panel placeholder text and the model viewer placeholder text are next to each other. It would be nice to have a visual separator between the two panels. The MUI package contains a nice widget to achieve this. A `Divider` widget draws a nice visual separator. It can be controlled to be either horizontal and vertical. 

To use this widget we first have to modify our split. We are now going to split it into 3 sections instead of 2. The first for the inputs panel, the second for the `Divider` and the third for the model viewer. We have to modify the `weights` as well. The number of `weights` should always match up with the number of sections. So we need 3 weights. The `Divider` also should be as small as possible. So we change the `weights` to `[0, 0, 1]` : 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

7/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

```
layout.Split(height='100%',
             weights=[0,0,1])[
'inputs panel',
'Divider placeholder',
'model viewer'
]
```

We can now replace the divider placeholder with the actual widget. We can obtain the `Divider` from the `mui` package. The `mui` package is a package that contains a lot of stylized widgets. 

## MUI package 

Make sure that the `mui` package is installed with 

```
pip install parapy-webgui-mui
```

Then the package can be imported using: 

```
fromparapy.webguiimport mui
```

We have to specify that the `Divider` should be vertically oriented, since by default it is horizontal. 

```
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            height='100%',
                            weights=[0,1])[
            AppBar(title="Stairs Configurator"),
            layout.Split(height='100%',
                         weights=[0,0,1])[
'inputs panel',
                mui.Divider(orientation='vertical'),
'model viewer'
]
]
```

We now have finished the initial layout of the app. We still have to replace the placeholder for the inputs panel and the model viewer. 

## Inputs panel 

For the inputs panel, we will create a new component. Evidently we already have quite some code inside our `App` component. It is good practice to create a component for each section to make reusable, readable and performant web apps. Up until now we have just used a single 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

8/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

component. Arguably we could have made a separate component for `content` . However, to not overcomplicate this tutorial we will only make a separate component for the inputs panel. 

```
classApp(Component):
defrender(self)-> NodeType:
return layout.Split(orientation='vertical',
                            height='100%',
                            weights=[0,1])[
            AppBar(title="Stairs Configurator"),
            layout.Split(height='100%',
                         weights=[0,0,1])[
                InputsPanel,
                mui.Divider(orientation='vertical'),
'model viewer'
]
]
classInputsPanel(Component):
defrender(self)-> NodeType:
return'Input panel placeholder'
```

We don't know exactly yet what we want to display in the inputs panel since we don't have our model yet. So we will park the development of the inputs panel until we know more about our model. 

## Model viewer 

Let's replace the model viewer with a geometry viewer widget. The `viewer` package contains a widget named `Viewer` . This widget allows the displaying of geometrical shapes. 

## Viewer package 

Make sure that the `viewer` package is installed with 

```
pip install parapy-webgui-viewer
```

Then the package can be imported using: 

```
fromparapy.webguiimport viewer
```

Let's replace the placeholder with this widget: 

 `class App(Component): def render(self) -> NodeType: return layout.Split(orientation='vertical', height='100%', weights=[0, 1])[ AppBar(title="Stairs Configurator"),` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

9/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`layout.Split(height='100%',`  `weights=[0, 0, 1])[ InputsPanel, mui.Divider(orientation='vertical'), viewer.Viewer, ] ]` 

When we now check our app, we can see a viewer has appeared. Nothing is being shown because we have not yet told the viewer what it should display. The viewer receives an `objects` argument that allows the user to provide objects that should be displayed. For now we will just add a `Cube` so we can check that it works. 

 

Import `Cube` from `parapy.geom` and provide it to the objects argument 

```
fromparapy.geomimport Cube
...
viewer.Viewer(objects=Cube(1))
...
```

A cube should now be visible in the viewer. We will replace this cube shortly with our model. 

## Summary 

You have now seen how you can divide the app in sections with `layout.Split` . You can then provide widgets from different libraries to create webpages. We will complete the inputs panel later once we have a model to control. 

The code app so far looks like this: 

**==> picture [454 x 11] intentionally omitted <==**

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

10/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

This is a preview of the demo, to get a live version install the documentation locally 

Expand code `1 class App(Component): 2 def render(self) -> NodeType: 3 return ( 4 layout.Split(orientation='vertical', 5 height='100%', 6 weights=[0, 1])[ 7 AppBar(title="Stairs Configurator"), 8 layout.Split(height='100%', 9 weights=[0, 0, 1])[ 10 InputsPanel, 11 mui.Divider(orientation='vertical'), 12 viewer.Viewer(objects=Cube(1)), 13 ] 14 ] 15 ) 16 17 18 class InputsPanel(Component): 19 def render(self) -> NodeType: 20 return 'Input panel placeholder'` 

## Creating a model 

We want to make a model of a stairs. The stairs should consist of the steps and a railing on each side. To create this model we will make use of the ParaPy modeling language, as well as 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

11/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

use the ParaPy geometry library. 

## ParaPy models 

This tutorial assumes that you have an entry level knowledge of the ParaPy modeling language. For more details on the modeling language, check out the ParaPy core tutorial 

Let's start by defining our model: 

```
fromparapy.coreimport Base
classStairs(Base):
pass
```

Now that we have a model, we will be defining the rules of that module using ParaPy Slots. There are three types of Slots: 

`Input` Slots are used to define the inputs of a model. 

- `Attribute` Slots are used to define properties of a model that are calculated. These 

- calculations are done lazily and are cached allowing for significant performance boosts. 

- `Part` Slots are used to define parent child relations. They allow you to define what a object 

- consists out of. 

## Inputs 

Since we are making a paremtric design, we want to define all the parameters that are required for the stairs. We can also add more inputs as we go, but we can already think of a few inputs that are required to model a stairs: 

```
height
```

```
width
step_height
```

```
step_depth
```

Let's add inputs for these parameters to our model. We can also guess some default values: 

```
fromparapy.coreimport Base, Input, Attribute, Part
classStairs(Base):
    height:float= Input(5)
    width:float= Input(1.5)
    step_height:float= Input(0.180)
    step_depth:float= Input(0.280)
```

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

12/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

## The steps 

To add the geometry for the steps to our model, we first need to have a strategy to create the geometry. There are multiple ways to achieve the desired geometry. Most likely the easiest approach is an extrusion. If we look at the stairs we can clearly see that the side profile of the stairs is just extruded along the width of the stairs. All we have to do is define the side profile outline and then extrude it: 

**==> picture [431 x 220] intentionally omitted <==**

First lets start by defining the points of the polygon. We can do this by making a `Attribute` in the model that returns a list of the points: 

```
classStairs(Base):
...
@Attribute
defsteps_outline_points(self):
        pts =[...]
return pts
```

We now have to come up with an algorithm that gets all the points. We will start by defining the first point. For this we select the most bottom left point and decide that this is the origin `(0, 0, 0)` . Then for each step we will add 2 points. Both these points have a `z` value of the `(step_index + 1) * step_height` . The `y` value of the first point is `step_index * step_depth` . The second will have a `y` value of `(step_index + 1) * step_depth` . 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

13/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

**==> picture [431 x 239] intentionally omitted <==**

Before we can make these point we first need to know how many steps are there in the stairs. So let's make a `Attribute` for that: 

```
classStairs(Base):
...
@Attribute
defnumber_of_steps(self):
returnint(self.height /self.step_height)
```

As you can see from the equation, we decide to round down the number of steps. Now that we have the number of step we can add points for each step in our outline `Attribute` . We now only have to add 2 more points that outline the backside of the stairs. We can see the coordinates in the scheme above for these points, namely: `(0, n * s_d, (n-1) * s_h)` and `(0, s_d, 0)` . 

## Point 

The `Point` class is used. This can be imported from the `parapy.geom` package: 

```
fromparapy.geomimport Point
```

The final algorithm looks like: 

 `@Attribute def steps_outline_points(self): pts = [Point()] s_h = self.step_height s_d = self.step_depth` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

14/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

```
    n =self.number_of_steps
# add 2 points for each step
for step_number inrange(n):
        z =(step_number +1)* s_h
        y1 = step_number * s_d
        y2 =(step_number +1)* s_d
        pts.append(Point(y=y1, z=z))
        pts.append(Point(y=y2, z=z))
# add 2 points for the backside of the steps
    pts.append(Point(y=n * s_d, z=(n -1)* s_h))
    pts.append(Point(y=s_d))
return pts
```

 

Let's now draw a line through them. For this we can use the `Polygon` from `parapy.geom` We can thus add a `Part` to our model, the `steps_outline` : 

`from parapy.geom import Polygon`  `class Stairs(Base): ... @Part def steps_outline(self): return Polygon(points=self.steps_outline_points)` 

Now that we have the outline. It would be nice to see it in the viewer we created earlier. If we create an instance of our stairs class, we can give it to the viewer to display: 

```
classStairs(Base):
...
# Stairs instance
STAIRS = Stairs()
classApp(Component):
...
        viewer.Viewer(objects=STAIRS)
...
```

The outline should now be visible. The points are not displayed because it is an `Attribute` . The Viewer by default only shows the `Part` slots of an object. If you would like to also display the points you can provide them to the `objects` argument of the `Viewer` manually: 

```
viewer.Viewer(objects=[STAIRS, STAIRS.steps_outline_points])
```

Now that we have an outline, lets extrude it. For this we add another `Part` to our model. Since we want to make a solid we can use the `ExtrudedSolid` class from `parapy.geom` . As input, we 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

15/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

provide the island to extrude, the direction and distance. For the direction we provide a `Vector` which points to the `x` direction. 

## ExtrudedSolid and Vector 

The `ExtrudedSolid` and `Vector` classes are used. These can be imported from the `parapy.geom` package. An in depth look on how the `ExtrudedSolid` class works can be found here. 

```
fromparapy.geomimport ExtrudedSolid, Vector
```

The solid can be added as such: 

```
classStairs(Base):
...
@Part
defsteps(self):
return ExtrudedSolid(island=self.steps_outline,
                             direction=Vector(x=1),
                             distance=self.width,
                             color=(200,200,200))
```

Now remember that we added the entire model to the `Viewer` earlier. The extrusion is now part of the model, so the viewer should update and the extruded steps should be visible. 

## The hand rails 

To build up the rails, we will first start by defining a path for the handrail. We will create this path by defining a polygonal wire. We will then fillet the corners to allow for the sweeping of a profile. To finish the handrail section, we will sweep a circular profile through the defined line. The supports are cylinders distributed over the length of the stairs. Finally, we will fuse the cylinders and handrail to make 1 single piece. That piece can then be mirrored to the other side of the stairs. 

**==> picture [431 x 98] intentionally omitted <==**

Let's start with the polygon defining the path of the handrail. We will have to provide a list of points to the polygon. The start and end point we have calculated before for the steps outline. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

16/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

The two upper points of the rail are the same points, but translated upwards with a set distance. We can add a new `Input` named `railing_height` for this variable. 

One additional note is that a `Polygon` by default closes the path. We have to tell it to not connect the last point with the first point. We can do this by setting `force_closure=False` . 

```
classStairs(Base):
...
    railing_height:float= Input(1.25)
...
@Part
defrough_rail_path(self):
return Polygon(
            points=[
                Point(),
                Point(z=self.railing_height),
                Point(y=self.number_of_steps *self.step_depth,
                      z=self.number_of_steps *self.step_height +
self.railing_height),
                Point(y=self.number_of_steps *self.step_depth,
                      z=self.number_of_steps *self.step_height),
],
            force_closure=False
)
```

The next step would be to fillet this polygonal wire we just created. We can use the `FilletedWire` from `parapy.geom` to achieve this. Create a new `Part` that returns a `FilletedWire` which receives the polygon we created as an argument. The second argument is the radius with which we would like to round the corners of the polygon. 

```
fromparapy.geomimport FilletedWire
classStairs(Base):
...
@Part
defrail_path(self):
return FilletedWire(built_from=self.rough_rail_path,
                            radius=0.1)
```

The result will be a nicely rounded wire. 

At this point the viewer will get starting cluttered with all the parts that we are making. That is because we are telling the `Viewer` widget to display the entire model. We can give it a subset of our model instead to have fine control of what should be displayed. In this case we would like to see the newly created filleted wire, but hide the rough polygon. To achieve this the `Viewer` widget inputs would look like this: 

```
viewer.Viewer(objects=[STAIRS.steps, STAIRS.rail_path])
```

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

17/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

The viewer can always be adjusted to inspect what we are currently making. 

Now that we have our path, we can create a profile and sweep it along the path to get our handrail. The `SweptSolid` receives a path and a profile as input. For the profile we can make a `Circle` . 

```
fromparapy.geomimport Circle, SweptSolid
classStairs(Base):
...
@Part
defrail_profile(self):
return Circle(radius=0.03)
@Part
defrail(self):
return SweptSolid(path=self.rail_path,
                          profile=self.rail_profile)
```

The result is our desired handrail path. Now the only thing missing are the supports. To get the supports we first have to make a distribution along the stairs where they should be placed. What we can do is create a `LineSegment` between the start and end point of our handrail path. We can then get an equally spaced point distribution on that line. If we do that we have the location of each of the support piles. 

To calculate the number of poles we would like to place, we introduce a new `Input` named `max_pole_distance` . This input will limit the maximum distance between the support poles. We then simply divide the length of the line, add one and round it down. 

A `LineSegment` has a method `equispaced_points` . This method returns a list of points equally spaced over the line. These inputs will include the start and end point, but we can strip those since our handrail already has a vertical feature at those locations. Lastly we can make sure that at least one support pole is always present by adding `n = max(3, n)` 

 `from parapy.geom import LineSegment class Stairs(Base): max_pole_distance: float = Input(1.) ... @Part def slope_line(self): return LineSegment(start=self.rail_path.start, end=self.rail_path.end) @Attribute def pole_points(self): n = int(self.slope_line.length / self.max_pole_distance + 1) n = max(3, n)` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

18/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

```
returnself.slope_line.equispaced_points(n)[1:-1]
```

 

Now we can place a cylinder on each of these points with the height equal to the `railing_height` . We have to specify that the `Part` we are creating is not just a single cylinder, but a multitude. For this we will use `quantify=len(self.pole_points)` . This means that the number of cylinders created will be equal to the length of the `pole_points` list. For the position of the cylinder we can create a `Position` object which receives for its location the point. To use the index of the "current" cylinder, we can use `child.index` . `child` can be imported from 

`parapy.core` . 

## child 

`child` is a unique ParaPy object which can be used in `@Part` expressions. They allow you to  reference the part that is generated. It is particularly useful for `@Part` expressions that use `quantify` , where child is the instance of the object that is created. You can then, for example, use `child.index` to get the index of the object currently being created. 

```
fromparapy.geomimport Cylinder
classStairs(Base):
...
@Part
defpoles(self):
return Cylinder(quantify=len(self.pole_points),
                        height=self.railing_height,
                        radius=0.03,
                        position=Position(self.pole_points[child.index]))
```

We now have all the subsections of our rail. Let's fuse it into a single solid. `FusedSolid` from `parapy.geom` does exactly this. It receives a shape and a number of tools to fuse on that shape. 

```
fromparapy.geomimport FusedSolid
classStairs(Base):
...
@Part
defrailing_left(self):
return FusedSolid(shape_in=self.rail,
                          tool=self.poles,
                          color=(230,80,20))
```

We now have our completed rail on the left. We can now mirror this rail to the right using `MirroredShape` , also imported from `parapy.geom` . We have to give the axis and reference point along which the shape is mirrored. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

19/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

```
fromparapy.geomimport MirroredShape
classStairs(Base):
...
@Part
defrailing_right(self):
return MirroredShape(shape_in=self.railing_left,
                             reference_point=Point(x=self.width /2),
                             vector1=VY,
                             vector2=VZ,
                             color=(230,80,20))
```

## VY and VZ 

`VY` and `VZ` are used. These are predefined unit vectors in the `Y` and `Z` axis. They can be imported from `parapy.geom` . Alternatively you could use the `Vector` object to create these vectors: 

```
vector1=Vector(0,1,0),
vector2=Vector(0,0,1),
```

And there we have it. The final stairs are complete. Let's make sure the viewer is displaying only the three final objects: 

```
viewer.Viewer(objects=[STAIRS.steps, STAIRS.railing_left, STAIRS.railing_right])
```

## Summary 

We used `parapy.core` to create a model. We filled this model with inputs, attributes and parts describing the model. To describe the geometry of the stairs we used some tools from the `parapy.geom` library. The model has been displayed in the viewer, by creating a global instance and providing the parts that we would like to show to the `Viewer` widget. 

The code of the app so far looks like this: 

**==> picture [454 x 11] intentionally omitted <==**

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

20/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

This is a preview of the demo, to get a live version install the documentation locally Expand code `1 class Stairs(Base):`  `2 height = Input(3) 3 width = Input(1.5) 4 5 step_depth = Input(0.280) 6 step_height = Input(0.180) 7 max_pole_distance = Input(1) 8 9 railing_height = Input(1.25) 10 11 @Attribute 12 def number_of_steps(self): 13 return int(self.height / self.step_height) 14 15 @Attribute 16 def steps_outline_points(self): 17 pts = [Point()] 18 s_h = self.step_height 19 s_d = self.step_depth 20 n = self.number_of_steps 21 for step_number in range(n): 22 z = (step_number + 1) * s_h 23 y1 = step_number * s_d 24 y2 = (step_number + 1) * s_d 25 pts.append(Point(y=y1, z=z)) 26 pts.append(Point(y=y2, z=z)) 27 pts.append(Point(y=n * s_d, z=(n - 1) * s_h)) 28 pts.append(Point(y=s_d))` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

21/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`29 return pts`  `30 31 @Part 32 def steps_outline(self):` 

## Input panel 

Now that we have a model, we can complete our app by filling in the inputs panel placeholder. 

Let's start by creating a plan for the panel. What we want is a number of fields below each other, each controlling an input. Additionally, we want a button that -when clicked- downloads a STEP file of the stairs. 

## Input panel layout 

The layout of the input panel is straightforward. It represents a vertical list of widgets. Previously we used `Split` to divide the area into sections. In this case we do not want to split the input panel area, but list the content. For this `Box` from the `parapy.webgui.layout` package can be used. The `Box` widget is similar to the `Split` widget. The difference is that the `Split` has weights to allow for the dividing of the available space, while `Box` simply lists its children. 

Let us replace the render function of our `InputsPanel` component with a `Box` . For the content of the box, we can use the `TextField` widget from the `parapy.webgui.mui` package. This widget is simply an input field. 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical')[
            mui.TextField,
            mui.TextField,
            mui.TextField,
]
```

When we look at the results, the text fields are very close to each other. There is also no spacing between the text fields and the border. We can adjust the styling of our `Box` to add these spacings. Specifically we want to change the `gap` value and the `padding` of the `Box` . 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

22/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

**==> picture [431 x 315] intentionally omitted <==**

For spacing between the children we can set the `gap` attribute. This accepts any css value in string format. For our case, let's set the gap between the text fields to `1em` , which is equal one text line height. 

We now have spacing, but we would also like some padding to the border. For this we will have to give the `Box` css styling. To give css styling to a widget, we can use the `style` argument. This accepts a dictionary with css properties. In this case we want to add padding, so we will use `style={"padding": "1em}` . 

The final Box styling looks like this: 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding':'1em'})[
            mui.TextField,
            mui.TextField,
            mui.TextField,
]
```

We now have the layout of the input panel as we would like. The next step is to make it so that the text fields update the model. 

## Controlling the model 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

23/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

In the previous step we added some text fields. Now we just have to update the model whenever the user changes these fields. 

There are some different approaches to achieve this. 

One approach is to provide the textfield with an event handler. An event handler is a function that is called whenever the event fires. In this case, we could listen to an `onChange` event. So whenever the user changes the value, the function is called. In this function we can use the new value to update the model. This is possible, but in this case we would have to do some manual processing of the value, since they will be returned as strings. There are also some edge cases that might be difficult to handle. 

A second approach is to use pre-fabricated widgets for interacting with parapy models. The `layout` package exposes a series of widgets for this exact purpose. These widgets are called `SlotField` widgets. There are a variety of them for different type of values. 

Let's use the second approach for our problem since we are dealing with a ParaPy model here. We can replace the first text field with a `SlotFloatField` . We can then link it to one of the inputs. For example the `height` input. A `SlotField` widget expects a model and a slot name to which it should be linked: 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding':'1em'})[
            layout.SlotFloatField(STAIRS,'height'),
            mui.TextField,
            mui.TextField,
]
```

The first input will now be a slot field. Try changing the value and then clicking away. The model displayed in the viewer should update everytime the user is done editing the value (clicks away). Now we can replace the remaining two textfields with other slots we would like to control. For example `width` and `max_pole_distance` : 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding':'1em'})[
            layout.SlotFloatField(STAIRS,'height'),
            layout.SlotFloatField(STAIRS,'width'),
            layout.SlotFloatField(STAIRS,'max_pole_distance'),
]
```

Now we have control over these three inputs. We can also reference some other parts from our model that are not inputs, but outputs. The `SlotField` will then become non-editable and only 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

24/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

displays the value. Let's add a field displaying the volume of the stairs. We can get the volume directly from the steps extrusion using `STAIRS.steps.volume` . We can then directly pass this to a display field like `mui.TextField` : 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding':'1em'})[
            layout.SlotFloatField(STAIRS,'height'),
            layout.SlotFloatField(STAIRS,'width'),
            layout.SlotFloatField(STAIRS,'max_pole_distance'),
            mui.TextField(value=STAIRS.steps.volume)
]
```

When we look at the labels of the slots, we see that by default the name of the attribute is used. It would be nice to give custom labels by providing the `label` argument: 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box(orientation='vertical',
                          gap='1em',
                          style={'padding':'1em'})[
            layout.SlotFloatField(STAIRS,'height', label='Height [m]'),
            layout.SlotFloatField(STAIRS,'width', label='Width [m]'),
            layout.SlotFloatField(STAIRS,'max_pole_distance', label='Maximum pole
distance [m]'),
            mui.TextField(value=STAIRS.steps.volume, label='Steps volume [m³]')
]
```

Whilst the result is what we were looking for, it would be nice to have the labels in front of the fields. So let's take a look on how to do this. The `mui` package has a lot of styled widgets, including widgets for the organization of forms. We can use a `FormControl` to make a group for each field. Then we can add a `FormLabel` widget to that group: 

 `class InputsPanel(Component): def render(self) -> NodeType: return layout.Box(orientation='vertical', gap='1em', style={'padding': '1em'})[ mui.FormControl[ mui.FormLabel['Height [m]'], layout.SlotFloatField(STAIRS, 'height'), ], mui.FormControl[ mui.FormLabel['Width [m]'], layout.SlotFloatField(STAIRS, 'width'), ], mui.FormControl[ mui.FormLabel['Maximum pole distance [m]'], layout.SlotFloatField(STAIRS, 'max_pole_distance'), ],` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

25/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`mui.FormControl[`  `mui.FormLabel['Steps volume [m³]'], mui.TextField(value=round(STAIRS.steps.volume, 3)), ], ]` If you check the result, it is almost what we were hoping for. There are now two overlapping labels. Let's tell the fields that they should not show a label by setting `show_label` to `False` : `... layout.SlotFloatField(STAIRS, 'height', show_label=False), ...` STEP file download The goal is to generate a step file from the stairs and allow the user to download it. We can get started by adding a button. For a button it is recommended to use the `Button` widget from the `parapy.webgui.mui` package. The `Button` widget has a variety of arguments to allow for customization. For a full overview of what you could do with a `Button` check out the muimui  

If you check the result, it is almost what we were hoping for. There are now two overlapping labels. Let's tell the fields that they should not show a label by setting `show_label` to `False` : 

## STEP file download 

The goal is to generate a step file from the stairs and allow the user to download it. We can get started by adding a button. For a button it is recommended to use the `Button` widget from the `parapy.webgui.mui` package. The `Button` widget has a variety of arguments to allow for customization. For a full overview of what you could do with a `Button` check out the muimui documentation. 

In our case we would like a `Button` of the `contained` variant. We can also give it some text as its child: 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box[
...
            mui.Button(variant='contained')[
"Download .STEP file"
]
]
```

Now that we have a button lets attach a function to it which we would like to be called whenever the user presses the button. To achieve this we can provide a function with an event which we would like to listen to. For the button we would like to listen to the `onClick` event: 

```
classInputsPanel(Component):
defrender(self)-> NodeType:
return layout.Box[
...
            mui.Button(variant='contained',
                       onClick=self.download_step)[
"Download .STEP file"
]
]
defdownload_step(self, evt):
print('button clicked!')
```

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

26/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

Let's take a closer look at this piece of code. First give an `onClick` argument to the button. We provide `onClick` with the function `self.download_step` . Note that we give the function, we are not calling the function: 

wrong: `onClick=self.download_step()` 

correct: `onClick=self.download_step` 

The button, whenever pressed, will look if there is a `onClick` argument. Then the function provided will be called. Thus whenever the user presses the button right now, the `download_step` method will be called. This method right now only print something to the console. 

A second thing to note it that the function receives an argument `evt` . This argument contains information about the event. Right now we don't plan to do anything with it. For textfield events this `evt` value contains the value of the textfield for example. 

Our goal now is to replace this printing with the behaviour of generating a step file and then let the user download it. 

Let's first generate a step file. To do this we can use the `STEPWriter` class from the `parapy.exchange` package. This class allows for the writing of a `.step` file given some geometry. In our case we want only the `step` , `railing_left` and `railing_right` to be writen to the step file. So lets provide that as a list to the writer: 

```
classInputsPanel(Component):
defdownload_step(self, evt):
        writer = STEPWriter([STAIRS.steps,
                             STAIRS.railing_left,
                             STAIRS.railing_right])
```

We now have a STEPWriter ready to write a `.step` file. We just have to provide it with a `file_path` to write to. 

Since we want the file to be downloaded by the user, we have to write it to the assets directory. The assets directory is a directory whose content can be accessed by users through the web. All other files cannot be accessed by the user for security reasons. So firstly let's check if we have an assets directory. 

By default, the WebGUI will look for an assets directory next to the file that is being executed: 

```
.
├── assets/
│   └── stairs.step
└── app.py
```

If this folder doesn't exist, then the WebGUI will not find it. You will have to create this folder for the WebGUI to automatically recognize it. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

27/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

Another option is to tell the WebGUI specifically the location of the assets directory. In the `display` function we can specify this value: 

```
if __name__ =='__main__':
fromparapy.webgui.coreimport display
    display(App, reload=True, assets_dir='/path/to/assets/dir')
```

It is however recommended to use the first option of auto discovery. 

Now that we have created an assets directory we can write our step file to that directory: 

```
fromparapy.webgui.coreimport get_assets_dir
...
classInputsPanel(Component):
...
defdownload_step(self, evt):
        writer = STEPWriter([STAIRS.steps,
                             STAIRS.railing_left,
                             STAIRS.railing_right])
        assets_dir = get_assets_dir()
        filename = os.path.join(assets_dir,'stairs.step')
        writer.write(filename)
```

Now whenever the button is clicked the `stairs.step` file should appear in the assets directory. The only thing left is to tell to the webpage that the file should be downloaded. 

We can use the `download_file(url)` function provided by the `parapy.webgui.core.actions` package to trigger this download. We just have to obtain a `url` to the file in the assets directory. To get this we can use the `get_asset_url` function. This function returns a url that points towards a file in the assets directory. All together this is what the function looks like: 

 `from parapy.webgui.core import get_assets_dir, get_asset_url from parapy.webgui.core.actions import download_file ... class InputsPanel(Component): def render(self) -> NodeType: ... def download_step(self, evt): writer = STEPWriter([STAIRS.steps, STAIRS.railing_left, STAIRS.railing_right])` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

28/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

 `assets_dir = get_assets_dir() filename = os.path.join(assets_dir, 'stairs.step') # write file to assets dir writer.write(filename) # get url and instruct to download the file behind the url url = get_asset_url(filename) download_file(url)` We now have a button that when clicked, downloads a step file of the current stairs model. Summary The app now has an inputs panel whereby the user can control the stairs model. We use `SlotFields` to directly interface with ParaPy models. The code app so far looks like this:  This is a preview of the demo, to get a live version install the documentation locally Expand code `1 class Stairs(Base):`  `2 height = Input(3) 3 width = Input(1.5) 4 5 step_depth = Input(0.280)` 

We now have a button that when clicked, downloads a step file of the current stairs model. 

## Summary 

The app now has an inputs panel whereby the user can control the stairs model. We use `SlotFields` to directly interface with ParaPy models. 

The code app so far looks like this: 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

29/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

`6 step_height = Input(0.180)`  `7 max_pole_distance = Input(1) 8 9 railing_height = Input(1.25) 10 11 @Attribute 12 def number_of_steps(self): 13 return int(self.height / self.step_height) 14 15 @Attribute 16 def steps_outline_points(self): 17 pts = [Point()] 18 s_h = self.step_height 19 s_d = self.step_depth 20 n = self.number_of_steps 21 for step_number in range(n): 22 z = (step_number + 1) * s_h 23 y1 = step_number * s_d 24 y2 = (step_number + 1) * s_d 25 pts.append(Point(y=y1, z=z)) 26 pts.append(Point(y=y2, z=z)) 27 pts.append(Point(y=n * s_d, z=(n - 1) * s_h)) 28 pts.append(Point(y=s_d)) 29 return pts 30 31 @Part 32 def steps outline(self):` 

## Reflection 

There are some aspects in the code we could improve on. 

Take a look at how the UI gets access to the model. With the current implementation we define a global instance of the model. Then each component directly grabs this instance whenever it is needed. This approach becomes problematic when making reusable components in a growing app. Right now none of the components we have created are truly reusable, since we would always have to change the pointer to the stairs. If we ever were to create another app that needs this inputs panel, we would also have to define a global stairs variable. This is not according to the WebGUI philosophy. 

This can be fixed by giving all components a `Prop` . Props are inputs for classes. When we give this prop we can provide components with values. In our case we would give a instance of `Stairs` to the `App` component: 

 `class App(Component): stairs: Stairs = Prop() ... if __name__ == '__main__': from parapy.webgui.core import display` 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

30/31 

4/27/26, 11:01 AM 

Creating an App - ParaPy Documentation 

 `STAIRS = Stairs() display(App(stairs=STAIRS), reload=True)` Now in the render function, we can pass this `self.stairs` to the child components that also `class App(Component): stairs: Stairs = Prop() def render(self) -> NodeType:`  `return ( layout.Split(orientation='vertical', height='100%', weights=[0, 1])[ AppBar(title="Stairs Configurator"), layout.Split(height='100%', weights=[0, 0, 1])[ InputsPanel(stairs=self.stairs), mui.Divider(orientation='vertical'), viewer.Viewer(objects=[self.stairs.steps, self.stairs.railing_left, self.stairs.railing_right]), ] ] ) class InputsPanel(Component): stairs: Stairs = Prop() ... if __name__ == '__main__': from parapy.webgui.core import display STAIRS = Stairs() display(App(stairs=STAIRS), reload=True)` 

Now in the render function, we can pass this `self.stairs` to the child components that also need it: 

Now the app and inputs panel components are reusable when it comes to the `Stairs` instance. 

## What is next? 

Next we would like to deploy our app to the cloud so that users can use it. When everything is set up, it is just a single command to push your app to the cloud. To learn more about the cloud go to the cloud tutorial. 

https://parapy.nl/docs/webgui/latest/learn/creating-an-app/ 

31/31 



# --- END OF SOURCE: Creating an App - ParaPy Documentation.pdf ---



# ========================================================
# START OF SOURCE: oop_pp_cheatsheet.pdf (Category: Parapy Documentation)
# ========================================================

## **“Plain” object-oriented vs. ParaPy code – cheat sheet** 

## **Changes in Code Structure** 

## **OOP code** 

```
importnumpyasnp
importmath
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

_unbound_ methods work in the same way (only useful if they’re “external” code or are also needed outside of the class) 

## **ParaPy code** 

```
importnumpyasnp
importmath
fromparapyimport core as ppc
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
```

```
    c_D0 =0.05/ (Re/1e+6)-*(1/5)  # accurately calibrated estimate!
return c_D0
```

```
classWing:
```

```
def-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):
self.A_ref = A_ref
self.b = b
self.phi_LE = phi_LE
self.alpha0 = alpha0
self.e = e
```

```
self.AR = b-*2/ A_ref
self.cD0 = estimate_cD0(A_ref, b, phi_LE)
self.clalpha =2+0* (self.AR +self.phi_LE)
```

```
defget_lift(self, alpha):
returnself.clalpha\
* (math.radians(alpha) - math.radians(self.alpha0))
```

```
defget_drag(self, cL):
```

```
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
return np.array(results)
```

```
testwing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = testwing.get_wing_lift(alpha)
cD = testwing.get_wing_drag(cL)
polar = testwing.get_polar(alphas_polar)
```

## No `-_init-_()` 

Input arguments are declared as class attributes (See also next page!) 

Internally-computed variables get their own @ `Attribute` methods, so they can be traced and computed separately, as needed 

„plain“ instance methods work exactly as they used to. Unless they require extra input or you _need_ to trigger them explicitly, it’s usually smarter to use @Attributes, though! 

creating an instance and calling its methods works exactly the same 

```
classWing_PP(ppc.Base):
    A_ref = ppc.Input()
```

```
    b = ppc.Input()
    phi_LE = ppc.Input(0)
    alpha0 = ppc.Input(0)
    e = ppc.Input(0.85)
```

```
@ppc.Attribute
defAR(self):
returnself.b-*2/self.A_ref
```

```
@ppc.Attribute
defcD0(self):
return estimate_cD0(self.A_ref, self.b, self.phi_LE)
```

```
@ppc.Attribute
defclalpha(self):
return2+0* (self.AR +self.phi_LE)
defget_lift(self, alpha):
returnself.clalpha\
* (math.radians(alpha) - math.radians(self.alpha0))
defget_drag(self, cL):
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
return np.array(results)
```

```
testwing_pp = Wing_PP(A_ref=30, b=20, phi_LE=15, alpha0=-0.5, e=0.85)
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = testwing_pp.get_wing_lift(alpha)
cD = testwing_pp.get_wing_drag(cL)
polar = testwing_pp.get_polar(alphas_polar)
```

## **“Plain” object-oriented vs. ParaPy code – cheat sheet** 

## **Differences in Data Handling** 

## **OOP code** 

```
importnumpyasnp
importmath
```

## **ParaPy code** 

```
importnumpyasnp
importmath
fromparapyimport core as ppc
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
```

```
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
```

```
    c_D0 =0.05/ (Re/1e+6)-*(1/5)  # accurately calibrated estimate!
return c_D0
```

## **`class`** `Wing::` 

**`class`** `Wing:: __init__()` is called **`def`** `-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):` implicitly at instantiation `self.A_ref = A_ref` and can calculate and `self.b = b` store whatever atttributes `self.phi_LE = phi_LE` are necessary for the `self.alpha0 = alpha0` object to work, as `self.e = e self.<attr>` 

`self.AR = b-*2 / A_ref self.cD0 = estimate_cD0(A_ref, b, phi_LE) __init__()` computes `self.clalpha = 2 + 0 * (self.AR + self.phi_LE)` intermediate variables once and stores results 

```
defget_lift(self, alpha):
returnself.clalpha\
```

```
* (math.radians(alpha) - math.radians(self.alpha0))
```

```
defget_drag(self, cL):
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
classWing_PP(ppc.Base):
```

The ParaPy base class adds its own `__init__()` which process all inputs, so you _should not_ write one! 

```
    A_ref = ppc.Input()
```

```
    b = ppc.Input()
```

```
    phi_LE = ppc.Input(0)
    alpha0 = ppc.Input(0)
    e = ppc.Input(0.85)
```

@ppc.Attribute definitions look like methods but can **do nothing** but compute one variable, and we never call them – so they’re **named after the variable** they compute 

```
@ppc.Attribute
```

Code to compute non-input attributes is declared in **`def`** `AR(self):` **`return`** `self.b-*2 / self.A_ref` separate methods. ParaPy finds their dependencies `@ppc.Attribute` and (re-)computes if (and **`def`** `cD0(self):(self):self):):` only if) needed. **`return`** `estimate_cD0(self.self..A_ref, self.b, self.phi_LE)` Y _ou never need to call these methods!_ 

```
defcD0(self):(self):self):):
return estimate_cD0(self.self..A_ref, self.b, self.phi_LE)
```

```
@ppc.Attribute
defclalpha(self):
return2+0* (self.AR +self.phi_LE)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
```

```
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
```

All methods defined within the class are available as instance attributes 

```
return np.array(results)
```

```
testwing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

The same, _except_ : **`def`** `get_lift(self, alpha):` ParaPy **@Attributes** **`return`** `self.clalpha\` **can’t be called directly** – `* (math.radians(alpha) - math.radians(self.alpha0))` you can only access their value, and ParaPy **`def`** `get_drag(self, cL):` ensures it’s updated **`return`** `self.cD0 + cL-*2 / (np.pi * self.AR * self.e)` 

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
return np.array(results)
```

## `cL = testwing.get_lift(alpha)` 

```
cD = testwing.get_drag(cL)
polar = testwing.get_polar(alphas_polar)
```

```
testwing.A_ref =10 # This is a terrible idea!
```

```
# …unless you write some extra code to make sure that
```

- _`# AR, cD0 and clalpha are updated afterwards…`_ 

If you change an input attribute after the fact, that can create an inconsistent state! 

ParaPy tracks when inputs change and updates the internal state as needed 

```
testwing_pp = Wing_PP(A_ref=30, b=20, phi_LE=15, alpha0=-0.5, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = testwing_pp.get_lift(alpha)
cD = testwing_pp.get_drag(cL)
polar = testwing_pp.get_polar(alphas_polar)
```

```
testwing_pp.A_ref =10
cD_new = testwing_pp.get_drag(cL)
```

## **Object-Oriented code structure – cheat sheet** 

## **Information flow** 

## **Outer scope** 

## **Inner scope** 

```
importnumpyasnp
importmath
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
```

The object returned includes all methods and other attributes defined in the class, including those defined by `__init__()` 

```
importnumpyasnp
```

## `[…]` 

## Object-specific data 

```
testwing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = testwing.get_lift(alpha)
cD = testwing.get_drag(cL)
```

```
polar = testwing.get_polar(alphas_polar)
```

## `print(testwing.clalpha)` 

```
# object-internal data remains available!
```

The outer scope provides the input data, once, and the object “knows” what to do with it. 

The object can be passed as an argument to other methods/classes, or even saved to disk and loaded later. 

## **Classes are** 

_**instantiated**_ **, not called!** This produces an _object_ which is an _instance_ of the class 

Instance methods can be _called_ , just like all other methods 

```
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated estimate!
return c_D0
```

```
<builtin __new__()>
```

```
# creates a new object
# adds all methods from the class
# calls its __init__() method
# returns the initialized object
```

```
classWing:
```

```
def-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):
self.A_ref = A_ref
self.b = b
self.phi_LE = phi_LE
self.alpha0 = alpha0
self.e = e
```

```
self.AR = b-*2/ A_ref
self.cD0 = estimate_cD0(A_ref, b, phi_LE)
self.clalpha =2+0* (self.AR +self.phi_LE)
```

All methods **inside** the class can access all _attributes_ and _methods_ as `self.<name>` 

```
defget_lift(self, alpha):
```

```
returnself.clalpha * (math.radians(alpha) -
                               math.radians(self.alpha0))
```

```
defget_drag(self, cL):
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
```

```
return np.array(results)
```

If we want to change inputs, it’s safer to create a new object: 

Direct inputs _and_ intermediate results are stored and are available to all internal methods 

```
testwing.A_ref =10# This is a terrible idea!
```

```
# …unless you write some extra code to make sure that
# AR, cD0 and clalpha are updated afterwards…
```

## _`# better:`_ 

```
testwing2 =  Wing(A_ref=10, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
# Now we can keep both wings around, and each wing contains its own data
```

## **ParaPy code structure – cheat sheet** 

## **Information flow** 

## **Outer scope** 

## **User-class scope** 

## **ParaPy-internal** 

## **`import math`** 

```
fromparapyimport core as ppc
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

As with OOP code, the object includes all methods, inputs and other attributes defined in the class (plus special ParaPy additions) 

```
importnumpyasnp
importmath
```

_Initial_ Input ParaPy classes are not too different from `=20, phi_LE=15,, phi_LE=15,=15,,` „normal“ classes 

```
testwing_pp = Wing_PP(A_ref=30, b=20, phi_LE=15,, phi_LE=15,=15,,
                      alpha0=-0.5, e=0.85)
```

```
alpha =1.5
```

```
alphas_polar = np.linspace(0, 3, num=16)
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)  # accurately calibrated estimate!
return c_D0
```

```
classWing_PP(ppc.Base):
```

```
    A_ref = ppc.Input()
    b = ppc.Input()
```

store input values or use use default 

```
    phi_LE = ppc.Input(0)
    alpha0 = ppc.Input(0)
    e = ppc.Input(0.85)
```

```
@ppc.Attribute
defAR(self):
returnself.b-*2/self.A_ref
```

```
parapy.core.Base
```

```
# …provides special __init__() method,
# registers Inputs, @Attributes, @Parts…
```

## `class Attribute(AbstractSlot):` 

```
# can be used just like a plain attribute in
# OOP, with a plain value (e.g. `self.AR`)
#
```

```
# …but actually:
```

## `cL = testwing_pp.get_lift(alpha)` 

```
cD = testwing_pp.get_drag(cL)
polar = testwing_pp.get_polar(alphas_polar)
```

```
@ppc.Attribute
defcD0(self):
```

```
return estimate_cD0(self.A_ref, self.b, self.phi_LE)
```

```
@ppc.Attribute
defclalpha(self):
return2+0* (self.AR +self.phi_LE)
```

```
# - stores the provided calculation method
```

```
# - computes value only(!) if needed, by
```

```
#   calling the calculation method
```

```
# - Stores the result for next time
```

```
# - Keeps a list of dependencies, to decide
```

- `#   when the stored value is outdated` 

## `print(testwing_pp.clalpha)` 

```
# object-internal data remains available!
```

```
defget_lift(self, alpha):
returnself.clalpha\
```

```
* (math.radians(alpha) - math.radians(self.alpha0))
```

```
defget_drag(self, cL):
```

```
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

The outer scope provides the input data, once, and the object “knows” what to do with it. 

… and we can assign new values to the inputs, without worrying about consistency! 

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
return np.array(results)
```

ParaPy registers all changes to Inputs and Attributes. Next time any dependent attributes (e.g. `AR` or `cD0)` are accessed, they are recomputed 

_Modified_ Input 

```
testwing_pp.A_ref =10
cD_new = testwing_pp.get_drag(cL)
```

The object is „augmented“ by ParaPy such that @Inputs and @Attributes are tracked and evaluated when needed, and only then. 

The class definition is mostly a declaration for ParaPy to construct a dependency graph and keep the object consistent when inputs change. 



# --- END OF SOURCE: oop_pp_cheatsheet.pdf ---



# ========================================================
# START OF SOURCE: ParaPy Tutorial 3.pdf (Category: Parapy Documentation)
# ========================================================

1 Positioning Para _Py_ objects 

The main classes for positioning are `Point(x, y, z)` , `Vector(x, y, z)` , `Orientation(vx, vy, vz)` and `Position(point, orientation)` . These classes provide their own set of attributes and methods. The most important functions for translation and rotation purposes, are `translate(point|position, dir, dist)` and `rotate(point|position, axis, angle)` . Refer to the separately provided “Positioning Cheatsheet” to get an immediate overview of the respective APIs. All class and function names are importable from the `parapy.geom` package. 

In ParaPy, primitive geometry can be located and oriented using an axis system. We refer to it as the object’s “position” in space. To specify the position of an object, you need to create a `Position` instance. A `Position` instance is a local axis system, defined by a location and orientation in Cartesian space. The global axis system is available in ParaPy as the constant `XOY` . Its location is fixed at `Point(0, 0, 0)` , available as constant `ORIGIN` . Its orientation equals the identity matrix `Orientation(x=Vector(1, 0, 0), y=Vector(0, 1, 0), z=Vector(0, 0, 1))` , available as constant `XY` . 

It is common practice in ParaPy, to create new `Position` instances relative to this global axis system by one or multiple translations and/or rotations. While rotation is a relatively straightforward principle, the key to translation is to appreciate that translation it is always relative to the orientation of the reference `Position` instance. The schematic below provides a high-level overview of this idea. This tutorial will guide you through it in a step-by-step fashion. 

```
p1 = translate(XOY, x=3, y=3, z=1)
p2 = rotate90(p1, 'z')
```

```
p3 = translate(p2, x=2)
```

**==> picture [146 x 90] intentionally omitted <==**

**==> picture [148 x 97] intentionally omitted <==**

**==> picture [161 x 114] intentionally omitted <==**

Classes that derive from `GeomBase` : 

## **`class`** `Aircraft(GeomBase):` 

inherit a `position` , `location` , `orientation` .[1] `GeomBase` was conceived to ease relative positioning of (sub-) assemblies. When creating child objects ( `@Part` ) that also derive from `GeomBase` , their `position` will be coupled to their parent’s `position` . This parent object can in turn be composed inside its own parent that also inherits from `GeomBase` and the same type of value binding occurs. As such, a tree of objects is created with coupled positions. If the root of the tree is re-positioned, the entire underlying object tree will translate and/or rotate accordingly. 

> 1 and a `bbox` (bounding box), but this isn’t part of this tutorial. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

Take a wing for example, it has a local axis system located at the wing root trailing edge point. Its x-axis corresponds to its chordwise direction and the y-axis to its spanwise direction. The root airfoil object could be positioned at this axis system, while a tip airfoil could be positioned relative to this axis system in y-direction over the wing span. If this wing would then later be composed as a right wing inside an aircraft, the wing could be placed at an offset from the aircraft’s coordinate system (the nose by convention) in both x- and y-directions. A high-level implementation of this in Para _Py_ could be like this: 

```
from parapy.core import *
from parapy.geom import *
class Aircraft(GeomBase):
    x_wing = Input(10)
    y_wing = Input(1)
    @Part
def right_wing(self):
return Wing(position=translate(self.position, 'x', self.x_wing, 'y', self.y_wing))
class Wing(GeomBase):
    span = Input(5)
    @Part
    def root_airfoil(self):
return Airfoil()
    @Part
def tip_airfoil(self):
return Airfoil(position=translate(self.position, 'y', self.span))
class Airfoil(GeomBase):
pass
>>> obj = Aircraft()
>>> obj.position.location
Point(0, 0, 0)
>>> obj.right_wing.position.location
Point(10, 1, 0)
>>> obj.right_wing.root_airfoil.position.location
Point(10, 1, 0)
>>> obj.right_wing.tip_airfoil.position.location
Point(10, 6, 0)
```

**==> picture [338 x 159] intentionally omitted <==**

**----- Start of picture text -----**<br>
z<br>x<br>y (10, 1, 0)<br>z<br>x<br>z<br>y (10, 6, 0) x<br>y (0, 0, 0)<br>**----- End of picture text -----**<br>


As witnessed, lower-level objects are relatively translated with respect to their parent object. The `root_airfoil` is somewhat special in that it wasn’t explicitly positioned at all, but still its position corresponds to that of the wing. This is because of _defaulting_ behavior in Para _Py_ . The standard behavior of the inherited `GeomBase.position` Input was defined to be defaulting: 

```
    position = Input(XOY, defaulting=True)
```

Unless given a different value, a _defaulting_ slot will trace up the object tree for a default value (first its direct parent, then the parent of that parent, etc.). If it finds any Slot with the same name, it will bind to that value. If it couldn’t find any similarly named Slot, it will take its own default value or raise a `MissingRequiredInput` exception if there was no default value. In case of `position` , you see that `root_airfoil` will find a “position” Slot in its parent wing object, while the aircraft has no parent and will default to the global axis system `XOY` . 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

As a general guideline, try to use relative positioning by inheriting `GeomBase` . Avoid hard-coding of object positions because it will seriously limit the re-usability of objects from an assembly perspective. 

## **Exercise 4: Boxes – positioning single objects** 

This tutorial will guide you through the positioning of single geometry objects. You will also learn how to read through some of the source codes of Para _Py_ . 

1. Create a new module and import the Para _Py_ geometry library with the following statement (at the top of your module): 

## **`from`** `parapy.geom` **`import`** `*` 

The advantage of a _wild_ import as opposed to other forms of import is that it imports _everything_ from the designated package or module at once. This allows using the various geometry variables, classes, and functions without prefixing them with the module's name.[2] During development in an IDE like PyCharm (and some other IDEs as well), the IDE will search through this library and provide you auto-completion suggestions based on what you are typing. For instance, if you are looking for a fit through a list of Points, type `Fit` . PyCharm will show all the Para _Py_ classes that have `Fit` in their name. Simply hitting enter will complete the class name in your editor. In general, try to exploit such features, they make you a productive programmer and prevent errors. 

**==> picture [301 x 59] intentionally omitted <==**

Similarly, if you are interested in all the classes with “Curve” in their name, type `Curve` . PyCharm will show all Curve classes. 

**==> picture [309 x 148] intentionally omitted <==**

2. Create a new class, say `MyClass` , and inherit from `GeomBase` : 

```
class MyClass(GeomBase):
```

3. Make a `Box` Part, called `box1` . 

```
    @Part
    def box1(self):
        return Box()
```

> 2 Importing everything from the `parapy.geom` package is considered safe practice. We took care of limiting what gets importing to a set of roughly 200 frequently used names. In general, however, importing everything from a module or package is discouraged. It may lead to namespace collisions (importing the same name from different modules), can be inefficient and is rather implicit programming. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

4. The `Box` object in Para _Py_ has three required inputs. You can either consult the API in the separately provided HTML documentation or you can quickly check what these inputs are by navigating to the declaration of Box inside the ParaPy source code. There are two ways to navigate to class declarations. If you prefer the mouse, hover over the word `Box` and, while holding _Ctrl_ , left-click the word. Alternatively, you can use the keyboard and type _Ctrl + B_ for this purpose. Verify that your editor jumps to the class definition inside `primitives.py` , as shown below: 

**==> picture [327 x 232] intentionally omitted <==**

The triple-quoted string immediately following the class statement is better known as a _docstring_ and will typically contain a short description of the class and provide a simple usage example. It may also prove convenient to quickly scan the entire API of a class using the _Structure_ window in PyCharm ( `Alt+7` ). Inputs are shown at the bottom as _fields_ , while Attributes and Parts are (wrongfully) shows as _methods_ . You can toggle the “Show inherited” button to visualize slots as inherited from ancestor classes. 

**==> picture [327 x 210] intentionally omitted <==**

On various occasions, you may notice an `__initargs__` assignment. This statement defines an additional, non-keyword-based constructor signature using positional arguments. For a `Box` it is perfectly valid to instantiate an object either following the defacto keyword-based notation 

```
>>> Box(width=1, length=2, height=3)
```

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

or to use a shorter notation with positional arguments 

```
>>> Box(1, 2, 3)
```

When using keywords, order doesn’t matter. The following line will give you the same result. 

```
>>> Box(length=2, height=3, width=1)
```

Finally, remaining Input should always follow positional arguments. 

```
>>> Box(1, 2, 3, color=”red”)
```

5. Pass the following arguments to `box1` : width=1, length=1 and height=1. Moreover, specify that is has the color red. 

6. Now let’s create another `Box` Part `box2` , similar in dimensions, but with a custom `position` input. Translate the position in x- and y-direction by 3: 

```
@Part
def box2(self):
return Box(width=1,
length=1,
height=1,
position=translate(self.position, 'x', 3, 'y', 3))
```

7. Rotate the position by 60 ° around the x-axis: 

```
@Part
def box2(self):
return Box(width=1,
length=1,
height=1,
position=rotate(translate(self.position, 'x', 3, 'y', 3),
                               Vector(1, 0, 0), radians(60)))
```

Note that the word `radians` in your editor is marked with a red line. You will need to import `radians` from the built-in `math` module. You can either type this import statement yourself at the top of your module, or, in case you are using PyCharm, locate your cursor on the word `radians` and press ALT+ENTER. The pop-up menu makes suggestions, one of which is to import this name: 

**==> picture [223 x 55] intentionally omitted <==**

Press enter again and select `math.radians(x)` . Pycharm will now add the following statement at the top of your module. 

```
from math import radians
```

Now, carefully look at the positioning syntax of the example above: 

```
position=rotate(translate(self.position, 'x', 3, 'y', 3),
                               Vector(1, 0, 0), radians(60)))
```

You can see that the result of `translate(self.position,` **`'x'`** `, 3,` **`'y'`** `, 3)` is used as the first argument to `rotate` . Why does this work? Functions like translate take a `Position` instance as first argument and return a new `Position` instances 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

as result. As such, you are passing the outcome of `translate` , a `Position` , as the first argument to `rotate` . In turn, `rotate` will return another `Position` instance that will be passed to the `Box` . 

8. Instantiate `MyClass` , and display it in the ParaPy GUI. Visualize `box1` and `box2` : 

**==> picture [227 x 97] intentionally omitted <==**

9. Make a third Box `box3` , like `box2` , but reverse the order of operations: a. first, rotate by 60 ° around the x-axis; b. then, translate in x- and y-direction by 3. 

10. Note the difference between `box2` and `box3` , due to the different order of translation and rotation steps: 

**==> picture [229 x 141] intentionally omitted <==**

## **Exercise 5: Staircase 1 – positioning quantified objects** 

This tutorial will guide you through the positioning and orienting of quantified geometry objects, applied to a simple staircase: 

**==> picture [227 x 141] intentionally omitted <==**

Use these inputs for the number of steps, width, length and thickness of individual steps, and the height between these: 

|**Staircase**|**Type **|**Value**|
|---|---|---|
|n_step|int|20|
|w_step|float|3|
|l_step|float|1|
|h_step|float|1|
|t_step|float|0.2|



1. Create a class and inherit `GeomBase` again. 

2. Define inputs per the table above. You may add a Python comment about the assumed units. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

3. As the number of steps is variable, you can’t predefine 20 individual box objects. Instead, we will use a quantified sequence of objects. This is done by specifying the `quantify` keyword as an input to your `Box` class. Refer to exercise 2 of the previous tutorial on how to use `quantify` . Create a `Part` that returns a sequence of `n_step Box` objects with dimensions equal to `w_step` , `l_step` and `t_step` . 

4. Position each `Box` object in your sequence. Translate each step position in y- and z-direction by the step width and height, respectively. You need the `child.index` syntax as explained in exercise 2. 

5. Color your steps. To do so, first add an Input slot to your class with a list of colors: 

```
colors = Input(["red", "green", "blue", "yellow", "orange"])
```

Then, pass the following argument to the return class of your steps Part: 

```
color=self.colors[child.index % len(self.colors)]
```

The `%` operator in Python, called modulo, will compute the remainder of dividing two numbers, x and y. It returns `x – int(x/y) * y` . As an example, consider x = 5, y = 2. Then `x%y = 5 – int(5/2) * 2 = 5 – 2 * 2 = 5 – 4 = 1` . 

## **Exercise 6: Staircase 2 – positioning quantified objects** 

Make a spiral version of your stair case that has exactly one revolution. Take a radius of 1. 

**==> picture [455 x 244] intentionally omitted <==**

2 Curve geometry 

## **Exercise 7: ParaPy curve classes, methods and attributes** 

All geometry is described by a mathematical model. Curves are parametrized in the form 𝑓(𝑢) −>  𝑃𝑜𝑖𝑛𝑡(𝑥, 𝑦, 𝑧), while surface are parametrized as 𝑓(𝑢, 𝑣) −>  𝑃𝑜𝑖𝑛𝑡(𝑥, 𝑦, 𝑧). B-Spline curves and surfaces in Para _Py_ are parameterized using the so-called Non-Uniform Rational Basis Spline, or NURBS representation. This model is often used in computer aided modelling due to its precise and well-known definition, flexibility in geometrical modelling and is the industry-standard method for exchange between different programs. Search the internet for a more in-depth overview of the underlying geometry. In short, Non-uniform rational basis spline means: 

- Basis Spline: curves and surfaces are controlled by a list or grid of 3D control points. 

- Rational: weights are used to affect the geometry. In case of a curve, each point on the curve is determined by taking a weighted sum of the control points. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

   - Non-Uniform: curves and surfaces have knot vectors that determine where and how the control points influence the NURBS geometry. 

- In this tutorial we will use the `BSplineCurve` class from the Para _Py_ geom library to construct several NURBS curves 

1. Create a class definition called `BSplineSamples` . 

2. In this class, create a list of points. The Points should have the following x-, y-, and z-coordinates: (0,0,0), (-3,3,0), (-11,3,0), (-15,0,0), (-11,-3,0), (-3,-3,0), (0,0,0). 

3. Check the required inputs for the `BSplineCurve` in the HTML docs or jump to its declaration. 

**==> picture [349 x 230] intentionally omitted <==**

4. Create a Part `curve` that returns an instance of type `BSplineCurve` and pass the list of points as its `control_points` . Beware of the common misconception that a B-Spline curve fits through the `control_points` . Generally, this is true for only the first and last control point, where the others act like “magnets” to the curve. If you actually need a curve that fits through all points, use the `FittedCurve` instead. 

5. Visualize both the `control_points` and the `BSplineCurve` in the GUI. You can visualize the `control_points` by right-clicking the `control_points` slot in the GUI property view and selecting “Display”. 

**==> picture [231 x 144] intentionally omitted <==**

6. A B-Spline curve has adjustable `weights` for closer approximations to arbitrary shapes. The default weight of a control point in Para _Py_ is 1.0 (this type of B-Spline curve is called non-rational). Modify the second weight value to 2.0 in the GUI. Observe the difference. Play with the other `weights` and observe the differences again 

7. Make another Part in the `BSplineSamples` class called `curves` that returns a sequence of 6 curves where the degree is varying from 1 to 6. Visualize the curves in the GUI. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

**==> picture [227 x 140] intentionally omitted <==**

8. Curve classes in Para _Py,_ such as `BSplineCurve` and `FittedCurve,` have several Attributes and methods that will make your life a lot easier when working with curve objects. These Attributes and methods can be found in the base class of all the Curve objects, called `Curve` . Navigate to its declaration. Once in curve.py, use the _Structure_ window in PyCharm ( `Alt+7` ). Clicking on Curve will bring you directly to the Curve class’ source code. 

**==> picture [207 x 229] intentionally omitted <==**

Typing _Ctrl + f_ and searching for “class Curve” will also bring you to the class. 

**==> picture [333 x 182] intentionally omitted <==**

Examples of attributes that you may find in this class are: `point1` , `midpoint` , `tangent2` and `normal1` . Examples of methods that you may find are: `projected_point` , `tangent` and `normal_at_point` . Try and find these Attributes and Methods. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

**==> picture [331 x 171] intentionally omitted <==**

9. Make an Attribute that returns a list of 30 equispaced points for each B-Spline curve in the sequence of varying-degree curves you made above. Since your Part returns a sequence of `BSplineCurve` objects, a for-loop or list comprehension should be used to access each individual curve. Use the method `equispaced_points` : 

```
crv.equispaced_points(30)
```

10. You can visualize your Attribute with the equispaced points in the tree by adding `(in_tree=True)` to the Attribute decorator. 

```
@Attribute(in_tree=True)
```

11. Check the equispaced point distributions in the GUI and verify that it display: 

**==> picture [228 x 143] intentionally omitted <==**

12. Determine the length of all your `BSplineCurve` objects in the GUI. Search for the `length` Attribute in the Attributes table of the GUI and evaluate the slot. Does the length increase or decrease with an increasing degree? 

13. Make an Attribute that returns a `Point` at length 2 of each `BSplineCurve` object. Use the Curve method `point_at_length` . 

```
crv.point_at_length(2)
```

14. Translate all `BSplineCurve` objects by 5 in z-direction. Your first thought might be to pass a translated position as argument to the `BSplineCurve` class. However, this will not work. ParaPy does not allow this, since there is no clear position or “axis system” for a B-Spline curve. Control points are taken relative to the global axis system. One way is to use the built-in method translated. Make a sequence of `TranslatedCurve` or `TransformedCurve` classes. These classes will also be used in later tutorials. 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

3 Surface geometry 

## **Exercise 8: ParaPy surface classes, methods and attributes** 

B-Spline curves are 1-dimensional parametric curves (its parameter is termed u) and require a flat list of control points. NURBS surfaces are 2-dimensional (its parameters are termed u and v) and require a list of lists, a 2-dimensional grid of control points. In this section, you will make a `BSplinceSurface` object. Just as for a `BSplinceCurve` in the previous example, it is in general not true that the `BSplineSurface` is fitted through all the control-points (see `FittedSurface` instead). 

1. Copy the following data: 

   - data = [ 

[(0, 0, 0), (3, 2, 0), (11, 2, 0), (15, 0, 0), (11, -1, 0), (3, -1, 0), (0, 0, 0)], 

[(0, 0, 5), (3, 2, 5), (13, 2, 5), (15, 0, 5), (13, -2, 5), (3, -2, 5), (0, 0, 5)], 

- [(0, 0, 10), (3, 2, 10), (11, 2, 10), (15, 0, 10), (11, -1, 10), (3, -1, 10), (0, 0, 10)]] 

Note that data consists of a list of three lists of tuples 

2. Transform this data into a list of three lists of `Point` objects. Note that you will need to use two for-loops since `data` is a list of lists. 

   - a. first, access each sub-list by looping through the outer list; 

   - b. then, access the tuples in each list and make `Point` objects from each tuple. 

   - c. `Append` the `Point` objects in a new list. 

   - d. `Append` this list to a new outer list. 

   - e. If you feel like a pro, use double list comprehension instead, this is shorter and faster. 

3. Make a surface with the `BSplineSurface` class. Specify its `control_points` . 

4. Visualize the `control_points` and the `BSplineSurface` in the GUI. 

**==> picture [228 x 140] intentionally omitted <==**

5. Just like curve classes _,_ surface classes in Para _Py_ have several Attributes and methods that will make your life a lot easier when working with surface objects. First, find the `Surface` base class. Then, find `area` , `point` , `u_tangent` and `cog` . 

6. Determine in the GUI the `area` of the surface, look under category Attributes in the GUI property view. 

7. Visualize the center of gravity ( `cog` ) of the `BSplineSurface` in the GUI. 

8. Make a new `Attribute` that returns the area of the surface. 

9. The Para _Py_ geometry library has many surface classes.  Look at this collection by typing “Surface” in the editor. PyCharm will show all the current Surface classes currently available in Para _Py_ . 

**==> picture [253 x 140] intentionally omitted <==**

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

4 Boolean operations 

## **Exercise 9: Boolean operations** 

Working in 3D usually involves the use of solid objects. At times, you may need to combine multiple parts into one, or remove sections from a solid. Para _Py_ has several Boolean operation classes that make this easy for you. In this example you will fuse, subtract, intersect and partition a box and cylinder with the following dimensions. 

|**Box**|**Type **|**Value**|
|---|---|---|
|height|float|1.0|
|width|float|1.0|
|length|float|1.0|



|**Cone**|**Type **|**Value**|
|---|---|---|
|radius1|float|0.5|
|radius2|float|0.2|
|height|float|1.5|



1. Define a class and make a `Box` and `Cone` Part. 

2. Position the Parts such that the `Cone` crosses the entire `Box` 

**==> picture [228 x 142] intentionally omitted <==**

3. Make a single solid from the `Box` and `Cone` objects by using the `FusedSolid` class with the `Cone` as tool and visualize it in the GUI. 

```
@Part
def fused(self):
return FusedSolid(shape_in=self.box,
tool=self.cone)
```

**==> picture [231 x 144] intentionally omitted <==**

4. Switch to the wireframe viewing mode by pressing “w” in the GUI viewport. Note the difference with the wireframe from step 2: edges are present at place where the `Cone` intersects the `Box` . 

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 

**==> picture [227 x 142] intentionally omitted <==**

5. Subtract the `Cone` from the `Box` with the `SubtractedSolid` class. 

**==> picture [227 x 140] intentionally omitted <==**

6. Determine the intersection between the `Box` and the `Cone` . Use the `CommonSolid` class. 

**==> picture [227 x 142] intentionally omitted <==**

7. The partition operation allows you to create different volumes in a shape. This may be convenient for assigning different materials to your shape or for multi-domain simulations with different, touching meshes. Create a partition by using the `PartitionedSolid` class. Note in the GUI both the PartionedSolid can be visualized (Display Node), but the separate volumes are also accessible as `solids` . Modify the `keep_tool` Input from False to True. 

**==> picture [228 x 142] intentionally omitted <==**

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright (c) 2016 - 2017 ParaPy B.V. & TU Delft 



# --- END OF SOURCE: ParaPy Tutorial 3.pdf ---



# ========================================================
# START OF SOURCE: Positioning Cheatsheet.pdf (Category: Parapy Documentation)
# ========================================================

**==> picture [160 x 92] intentionally omitted <==**

```
Point(x=0, y=0, z=0)
```

## Positioning Cheatsheet 

```
Position(location=ORIGIN, orientation=XY)
```

```
>>> pt1 = Point(1, 2, 3)
>>> pt2 = Point(3, 4, 5)
>>> pt1[0]
1
>>> pt1.x
1
```

```
>>> for i in pt1:
print i,
```

```
1 2 3
>>> list(pt1)
[1, 2, 3]
>>> -pt1
Point(-1, -2, -3)
>>> pt2 -pt1
Vector(2, 2, 2)
>>> pt1 -pt2
Vector(-2, -2, -2)
>>> pt1.distance(pt2)
3.46...
>>> pt1.midpoint(pt2)
Point(2, 3, 4)
>>> pt1.interpolate(pt2, 0.75)
Point(2.5, 3.5, 4.5)
>>> pt1.translate(x=1)
Point(2, 2, 3)
>>> pt1.rotate('z', pi/2)
>>> pt1.rotate('z', 90, deg=True)
>>> pt1.rotate90('z')
Point(-2, 1, 3)
>>> pt1.rotate_around(pt2, 'z', pi/2)
>>> pt1.rotate_around(pt2, 'z', 90, deg=True)
>>> pt1.rotate90_around(pt2, 'z')
Point(5, 2, 3)
>>> pt1.project(pt2, 'z')
Point(3, 4, 3)
>>> pt1.project(pt2, 'y', 'z')
Point(3, 2, 3)
>>> pt1.polygon('x', 1, 'y', 2)
[Point(1, 2, 3), Point(2, 2, 3), Point(2, 4, 3)]
>>> ORIGIN
Point(0, 0, 0)
```

**==> picture [324 x 102] intentionally omitted <==**

```
>>> p1 = Position(pt1, XY)
>>> p2 = Position(pt1, YZ)
>>> p1[0], p1.x
1, 1
>>> p1.location
Point(1, 2, 3)
>>> p2.orientation
Orientation(x=Vector(0.0, 1.0, 0.0),
y=Vector(0.0, 0.0, 1.0),
z=Vector(1.0, 0.0, 0.0))
```

```
>>> p1.Vx, p1.Vy
(Vector(1, 0, 0), Vector(0, 1, 0))
>>> p2.Vx, p2.Vy
(Vector(0, 1, 0), Vector(0, 0, 1))
>>> p1.translate(x=1), p2.translate(x=1)
(Position(2, 2, 3), Position(1, 3, 3))
>>> p1.get_point(x=1), p2.get_point(x=1)
(Point(2, 2, 3), Point(1.0, 3.0, 3.0))
>>> XOY, YOZ, ZOX
...
```

```
translate(p, v1, s1[, v2, s2, ...])
```

```
>>> pt= Point(1, 0, 0)
>>> translate(pt, 'x', 1)
Point(2, 0, 0)
>>> translate(pt, x=1)
Point(2, 0, 0)
>>> translate(pt, Vector(1, 0, 0), 1)
Point(2, 0, 0)
>>> translate(pt, 'x', 1, 'y', 1)
Point(2, 1, 0)
```

```
>>> pos = Position(pt).rotate90('z')
>>> translate(pos, 'x', 1)
Position(1, 1, 0)
>>> translate(pos, x=1)
Position(1, 1, 0)
```

```
>>> translate(pos, Vector(1, 0, 0), 1)
Position(2, 0, 0)
>>> translate(pos, 'x', 1, 'y', 1)
Point(0, 1, 0)
```

```
rotate(p, dir, angle[, ref=q, deg=bool])
rotate90(p, dir, [, ref=q, deg=bool])
```

```
>>> p1 = translate(XOY, x=3, y=3, z=1)
>>> p1.location
Point(3, 3, 1)
>>> p1.Vx
Vector(1, 0, 0)
>>> p2 = rotate90(p1, 'z')
>>> p2.Vx
Vector(0,0, 1.0, 0.0)
>>> p3 = translate(p2, x=2)
>>> p3.location
Point(3.0, 5.0, 1.0)
>>> p3.Vx
Vector(0,0, 1.0, 0.0)
```

```
>>> pt= Point(1, 0, 0)
>>> rotate(pt, 'z', pi/2.)
Point(0, 1, 0)
>>> rotate(pt, 'z', radians(90))
Point(0, 1, 0)
>>> rotate(pt, 'z', 90, deg=True)
Point(0, 1, 0)
```

```
>>> pt= Point(1, 0, 0)
>>> rotate90(pt, 'z')
Point(0, 1, 0)
>>> rotate90(pt, 'z', ref=Point(0.5, 0, 0))
Point(0.5, 0.5, 0.0)
```

The information enclosed is proprietary and is provided to you on a strictly confidential basis. Copyright © 2016-2017 ParaPy B.V. 

**==> picture [756 x 41] intentionally omitted <==**



# --- END OF SOURCE: Positioning Cheatsheet.pdf ---



# ========================================================
# START OF SOURCE: proc_oop_cheatsheet - Copy.pdf (Category: Parapy Documentation)
# ========================================================

Alexander Heidebrecht 

v2026.1 26.02.2026 

## **Procedural vs. Object-oriented Code – Cheat Sheet** 

## **Changes in code structure** 

## **Procedural code** 

```
importnumpyasnp
importmath
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

_unbound_ methods can still be used (Only useful if they also have other uses outside of the class) 

## **OOP code** 

```
importnumpyasnp
```

## **`import math`** 

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

```
defget_wing_cLalpha(AR, phi_LE):
return2+0* (AR + phi_LE)
```

```
defget_wing_lift(alpha, AR, phi_LE, alpha0):
    clalpha = get_wing_cLalpha(AR, phi_LE)
return clalpha * (math.radians(alpha) - math.radians(alpha0))
```

```
defget_wing_drag(cD0, e, AR, cL):
return cD0 + cL-*2/ (np.pi * AR * e)
```

```
defget_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas):
    AR = b-*2/ A_ref
```

```
    cD0 = estimate_cD0(A_ref, b, phi_LE)
```

```
    results = []
```

```
for alpha in alphas:
```

```
        cL = get_wing_lift(alpha, AR, phi_LE, alpha0)
        cD = get_wing_drag(cD0, e, AR, cL)
        results.append([cL, cD])
```

```
return np.array(results)
```

```
A_ref =30# wing reference area
b =20# span (m)
phi_LE =15# LE sweep angle (°)
alpha0 =-0.6# zero lift AoA (°)
e =0.85# Oswald factor
```

methods that are related directly to the Object become _instance_ methods: They move inside the class, can be accessed as attributes of an object (the _instance_ of the class) 

Variables specifying object-specific values are provided once at object creation and can then be processed and stored as attributes by the `__init__()` method. There’s no need for the outer scope to store them. 

## **`class`** `Wing:` 

```
def-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):
self.A_ref = A_ref
```

```
self.b = b
```

```
self.phi_LE = phi_LE
self.alpha0 = alpha0
self.e = e
```

```
self.AR = b-*2/ A_ref
self.cD0 = estimate_cD0(A_ref, b, phi_LE)
self.clalpha =2+0* (self.AR +self.phi_LE)
```

```
defget_lift(self, alpha):
```

```
returnself.clalpha * (math.radians(alpha) -
 math.radians(self.alpha0))
```

```
defget_drag(self, cL):
```

```
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
```

```
return np.array(results)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cD0 = estimate_cD0(A_ref, b, phi_LE)
AR = b-*2/ A_ref
```

```
cL = get_wing_lift(alpha, AR, phi_LE, alpha0)
cD = get_wing_drag(cD0, e, AR, cL)
```

```
polar = get_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas_polar)
```

Intermediate results that don’t change can be computed during initialisation and stored in the object 

```
thiswing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = thiswing.get_wing_lift(alpha)
cD = thiswing.get_wing_drag(cL)
```

```
polar = thiswing.get_polar(alphas_polar)
```

## **Procedural vs. Object-oriented Code – Cheat Sheet** 

# **Differences in data handling** 

## **Procedural code** 

```
importnumpyasnp
importmath
```

```
importnumpyasnp
importmath
```

## **OOP code** 

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
```

```
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

```
defget_wing_cLalpha(AR, phi_LE):
return2+0* (AR + phi_LE)
```

```
defget_wing_lift(alpha, AR, phi_LE, alpha0):
    clalpha = get_wing_cLalpha(AR, phi_LE)
```

```
return clalpha * (math.radians(alpha) - math.radians(alpha0))
```

```
defget_wing_drag(cD0, e, AR, cL):
return cD0 + cL-*2+ cL-*2 cL-*2-*2/ (np.pi * AR * e) (np.pi * AR * e).pi * AR * e)pi * AR * e)* AR * e) AR * e)* e) e)
```

**`return`** `cD0 + cL-*2+ cL-*2 cL-*2-*2 / (np.pi * AR * e) (np.pi * AR * e).pi * AR * e)pi * AR * e)* AR * e) AR * e)* e) e)` methods are “unbound”, require all relevant data **`def`** `get_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas):` as call arguments `AR = b-*2 / A_ref cD0 = estimate_cD0(A_ref, b, phi_LE)` 

```
    results = []
for alpha in alphas:
```

```
        cL = get_wing_lift(alpha, AR, phi_LE, alpha0)
        cD = get_wing_drag(cD0, e, AR, cL)
        results.append([cL, cD])
```

Object-specific data is defined and stored in the “outer” scope… 

```
return np.array(results)
```

```
A_ref =30# wing reference area
b =20# span (m)
```

```
phi_LE =15# LE sweep angle (°)
alpha0 =-0.6# zero lift AoA (°)
e =0.85# Oswald factor
```

```
alpha =1.5
```

...and needs to be provided for every function call 

```
alphas_polar = np.linspace(0, 3, num=16)
```

```
cD0 = estimate_cD0(A_ref, b, phi_LE)
AR = b-*2/ A_ref
```

`__init__()` is called implicitly at instantiation and can calculate and store whatever atttributes are necessary for the object to work, as `self.<attr>` 

```
classWing:
```

```
def-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):
self.A_ref = A_ref
self.b = b
self.phi_LE = phi_LE
self.alpha0 = alpha0
self.e = e
```

```
self.AR = b-*2/ A_ref
self.cD0 = estimate_cD0(A_ref, b, phi_LE)
self.clalpha =2+0* (self.AR +self.phi_LE)
```

Instance methods implicitly receive `self` as first argument and can access all instance attributes 

```
defget_lift(self, alpha):
returnself.clalpha\
* (math.radians(alpha) - math.radians(self.alpha0))
```

```
defget_drag(self, cL):
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
```

Object-specific data is provided once during instantiation and stored in the resulting object 

All methods defined within the class are available as instance attributes 

```
return np.array(results)
```

**This object contains the** `testwing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)` **data** _**and**_ **the correct methods needed for the** `alpha == 1.5` **functionality.** `= np.linspace(0, 3, num=16)) .linspace(0, 3, num=16)) 0, 3, num=16)) 3, num=16)) =16))` 

```
alpha ==1.5
alphas_polar = np.linspace(0, 3, num=16))
```

```
cL = get_wing_lift(alpha, AR, phi_LE, alpha0)
cD = get_wing_drag(cD0, e, AR, cL)
```

```
cL = testwing.get_lift(alpha)
cD = testwing.get_drag(cL)
```

```
polar = get_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas_polar)
```

```
polar = testwing.get_polar(alphas_polar)
```

Outer scope needs to Methods names are “know” which methods **verbs** because are appropriate methods _do_ something 

The class name and the name of the object are **nouns** because they describe objects 

Methods names inside in the class are still **verbs** because they specify what an object of this class _does._ 

## **Procedural code structure – cheat sheet** 

# **Information flow** 

**“Outer” scope (use-case specific)** 

```
importnumpyasnp
importmath
[…]
```

`A_ref = 30` _`# wing reference area`_ `b = 20` _`# span (m)`_ Object-specific data `phi_LE = 15` _`# LE sweep angle (°)`_ `alpha0 = -0.6` _`# zero lift AoA (°)`_ `e = 0.85` _`# Oswald factor`_ Methods are _called_ Analysis-specific data (and may return `alpha = 1.5` something) `alphas_polar = np.linspace(0, 3, num=16) cD0 = estimate_cD0(A_ref, b, phi_LE) AR = b-*2 / A_ref` 

```
cL = get_wing_lift(AR, phi_LE, alpha0, alpha)
cD = get_wing_drag(cD0, e, AR, cL)
polar = get_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas_polar)
```

**“Inner” scope (Core functionality)** 

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
    Re =1e+6* c_ref  # representative Reynolds number
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated!
return c_D0
```

```
defget_wing_cLalpha(AR, phi_LE):
return2+0* (AR + phi_LE)
```

```
defget_wing_lift(alpha, AR, phi_LE, alpha0):
    clalpha = get_wing_cLalpha(AR, phi_LE)
return clalpha * (math.radians(alpha) - math.radians(alpha0))
```

```
defget_wing_drag(cD0, e, AR, cL):
return cD0 + cL-*2/ (np.pi * AR * e)
```

```
defget_wing_polar(A_ref, b, phi_LE, alpha0, e, alphas):
    AR = b-*2/ A_ref
```

```
    cD0 = estimate_cD0(A_ref, b, phi_LE)
```

```
    results = []
```

```
for alpha in alphas:
```

```
        cL = get_wing_lift(alpha, AR, phi_LE, alpha0)
        cD = get_wing_drag(cD0, e, AR, cL)
        results.append([cL, cD])
```

```
return np.array(results)
```

The outer scope provides the input data, every time it’s used. 

We can change data as we like but we also must take care to keep it consistent, including intermediate results. 

The “inner” scope has no memory stores no intermediate results Relies on user to provide correct inputs for every calculation 

**==> picture [209 x 56] intentionally omitted <==**

## **Object-Oriented code structure – cheat sheet** 

## **Information flow** 

## **Outer scope** 

## **Inner scope** 

```
importnumpyasnp
importmath
```

```
defestimate_cD0(A_ref: float, b: float, phi_LE: float) ->float:
    c_ref = A_ref / b  # mean chord length
```

```
    Re =1e+6* c_ref  # representative Reynolds number
```

The object returned includes all methods and other attributes defined in the class, including those defined by `__init__()` 

```
importnumpyasnp
```

## `[…]` 

## Object-specific data 

```
testwing = Wing(A_ref=30, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
alpha =1.5
alphas_polar = np.linspace(0, 3, num=16)
```

```
cL = testwing.get_lift(alpha)
cD = testwing.get_drag(cL)
```

```
polar = testwing.get_polar(alphas_polar)
```

## `print(testwing.clalpha)` 

```
# object-internal data remains available!
```

The outer scope provides the input data, once, and the object “knows” what to do with it. 

The object can be passed as an argument to other methods/classes, or even saved to disk and loaded later. 

## **Classes are** 

_**instantiated**_ **, not called!** This produces an _object_ which is an _instance_ of the class 

Instance methods can be _called_ , just like all other methods 

```
    c_D0 =0.05/ (Re/1e+6)-*(1/5)# accurately calibrated estimate!
return c_D0
```

```
<builtin __new__()>
```

```
# creates a new object
# adds all methods from the class
# calls its __init__() method
# returns the initialized object
```

```
classWing:
```

```
def-_init-_(self, A_ref, b, phi_LE=0, alpha0=0, e=0.85):
self.A_ref = A_ref
self.b = b
self.phi_LE = phi_LE
self.alpha0 = alpha0
self.e = e
```

```
self.AR = b-*2/ A_ref
self.cD0 = estimate_cD0(A_ref, b, phi_LE)
self.clalpha =2+0* (self.AR +self.phi_LE)
```

All methods **inside** the class can access all _attributes_ and _methods_ as `self.<name>` 

```
defget_lift(self, alpha):
```

```
returnself.clalpha * (math.radians(alpha) -
                               math.radians(self.alpha0))
```

```
defget_drag(self, cL):
returnself.cD0 + cL-*2/ (np.pi *self.AR *self.e)
```

```
defget_polar(self, alphas) -> np.array:
        results = []
for alpha in alphas:
            cL =self.get_lift(alpha)
            cD =self.get_drag(cL)
            results.append([cL, cD])
```

```
return np.array(results)
```

If we want to change inputs, it’s safer to create a new object: 

Direct inputs _and_ intermediate results are stored and are available to all internal methods 

```
testwing.A_ref =10# This is a terrible idea!
```

```
# …unless you write some extra code to make sure that
# AR, cD0 and clalpha are updated afterwards…
```

## _`# better:`_ 

```
testwing2 =  Wing(A_ref=10, b=20, phi_LE=15, alpha0=-0.6, e=0.85)
```

```
# Now we can keep both wings around, and each wing contains its own data
```



# --- END OF SOURCE: proc_oop_cheatsheet - Copy.pdf ---



# ========================================================
# START OF SOURCE: Tutorial 2 ParaPy classes and GUI.pdf (Category: Parapy Documentation)
# ========================================================

**==> picture [50 x 162] intentionally omitted <==**

## **Knowledge Based Engineering (KBE) AE4202** 

**Tutorial 2 Dr.ir. G. La Rocca** _FPP_ Python vs. ParaPy object oriented programming **Dr.-Ing. A. Heidebrecht** The ParaPy `classes` _FPP_ • 

- `Input(), @Input` 

- `@Attribute` 

- `@Part` 

**==> picture [960 x 136] intentionally omitted <==**

**----- Start of picture text -----**<br>
Class structure<br>**----- End of picture text -----**<br>


**==> picture [960 x 58] intentionally omitted <==**

**==> picture [50 x 162] intentionally omitted <==**

## **Agenda** 

- Python classes 

- ParaPy classes 

- ParaPy GUI 

Exercise 2 on Python classes Exercise 3 on ParaPy classes 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

2 

**==> picture [50 x 162] intentionally omitted <==**

## **Typical Python Class Layout** 

**`class`** `MyClass(Superclass):` _`# inherit from Superclass`_ `foo = 1` _`# class attribute`_ **`def`** `bar(self):` _`# methods...`_ **`return`** `self.foo + 1` **`def`** `quz(self): =` **`return`** `Box(width self.bar)` **`def`** `qux(self, spam):` **`print(`** `spam` **`)`** indentation extra arguments 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

3 

**==> picture [50 x 162] intentionally omitted <==**

## **Python classes** 

**==> picture [313 x 70] intentionally omitted <==**

**----- Start of picture text -----**<br>
class  Wing():<br>taper = 0.2<br>c_root = 4<br>Class variables<br>def  get_c_tip(self):<br>**----- End of picture text -----**<br>


```
print("I take 10 minutes to return“)
return self.c_root * self.taper
```

**==> picture [95 x 14] intentionally omitted <==**

**----- Start of picture text -----**<br>
Class method<br>**----- End of picture text -----**<br>


```
>>>wing = Wing()
```

**`>>>`** `wing.get_c_tip()` **`"I take 10 minutes to return"`** `0.8` **`>>>`** `wing.get_c_tip()` non-caching **`"I take 10 minutes to return"`** `0.8` **`>>>`** `wing.taper = 0.3` **`>>>`** `wing.get_c_tip()` **`"I take 10 minutes to return"`** `1.2` 

**==> picture [91 x 56] intentionally omitted <==**

## Class initialization method 

```
class Wing():
```

```
def __init__(self, taper=0.2, c_root=4):
self.taper = taper
self.c_root = c_root
self.c_tip = self.get_c_tip()
```

```
def get_c_tip(self):
print("I take 10 minutes to return")
return self.c_root * self.taper
```

**==> picture [399 x 198] intentionally omitted <==**

**----- Start of picture text -----**<br>
>>> wing = Wing()<br>"I take 10 minutes to return“<br>>>> wing.c_tip non-lazy<br>0.8 caching<br>>>> wing.c_tip<br>0.8<br>>>> wing.taper = 0.3 no dependency<br>>>> wing.c_tip<br>tracking<br>0.8<br>>>> wing.c_tip = wing.get_c_tip()<br>"I take 10 minutes to return“<br>>>> wing.c_tip non-lazy<br>1.2<br>**----- End of picture text -----**<br>


**==> picture [93 x 50] intentionally omitted <==**

Test it yourself with AE4204 Knowledge Based Engineering (K `classes.py` on rightspace **B** E) 

4 

**==> picture [50 x 162] intentionally omitted <==**

## **Typical Python Class Layout** 

```
class MyClass(Superclass):              # inherit from Superclass
foo = 1                             # class attribute
```

```
def bar(self):                      # methods...
return self.foo + 1
def quz(self):
=
return Box(widthself.bar)
def qux(self, spam):
print(spam)
```

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

5 

**==> picture [50 x 162] intentionally omitted <==**

## **Typical Para** _**Py**_ **Class Layout** 

**`class`** `MyClass(` **`Base,`** `Superclasses):` _`# inherit from ParaPy Base`_ `foo =` **`Input`** `(1)` _`# Input`_ **`@Attribute`** _`# Attribute`_ **`def`** `bar(self):` decorator **`return`** `self.foo + 1` **`@Part`** _`# Part`_ **`def`** `quz(self):` decorator `=` **`return`** `Box(width self.bar)` **`def`** `qux(self, spam):` _`# method`_ **`print(`** `spam` **`)`** 

**==> picture [91 x 56] intentionally omitted <==**

6 

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

**==> picture [50 x 162] intentionally omitted <==**

## **Para** _**Py**_ **adds dependency tracking, caching and lazy evaluation** 

## ParaPy Class 

## Python Class 

```
class Wing():
taper = 0.2
c_root = 4
```

```
class Wing(Base):
taper = Input(0.2)
c_root = Input(4)
@Attribute
def c_tip(self):
print("I take 10 minutes to return“)
return self.c_root * self.taper
```

```
def get_c_tip(self):
print("I take 10 minutes to return“)
return self.c_root * self.taper
```

**==> picture [831 x 204] intentionally omitted <==**

**----- Start of picture text -----**<br>
>>> wing = Wing() >>> wing = Wing()<br>>>> wing.get_c_tip() >>> wing.c_tip lazy<br>"I take 10 minutes to return" "I take 10 minutes to return"<br>0.8 0.8<br>>>>  wing.get_c_tip() >>> wing.c_tip caching<br>"I take 10 minutes to return" 0.8<br>0.8 >>> wing.taper = 0.3 lazy<br>>>>  wing.taper = 0.3 >>> wing.c_tip<br>>>>  wing.get_c_tip() "I take 10 minutes to return"<br>"I take 10 minutes to return" 1.2<br>1.2<br>dependency<br>tracking<br>**----- End of picture text -----**<br>


**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

Test it yourself with AE4204 Knowledge Based Engineering (K `classes.py` on rightspace **B** E) 

7 

**==> picture [50 x 162] intentionally omitted <==**

## **Input() and @Input: inputs to your ParaPy class object** 

```
class MyClass(Base):
```

no default 

Use only if you actually have a good default! 

```
foo= Input()               # requiredinput
foo= Input(<default>)      # optionalinput (simple)
```

**`@Input`** _`# optional input (derived)`_ **`def foo(self): return`** _`<expression>`_ different syntax, allows adaptive 

different syntax, allows adaptive defaults (e.g. rule of thumb for sensible starting values) 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

9 

**==> picture [50 x 162] intentionally omitted <==**

**==> picture [91 x 56] intentionally omitted <==**

## **Input examples** 

```
class Wing(Base):
span = Input()
AR = Input()
c_root = Input(4.0)
```

**==> picture [109 x 55] intentionally omitted <==**

**----- Start of picture text -----**<br>
This is not a<br>good default…<br>(see next slide)<br>**----- End of picture text -----**<br>


```
@Input()
def c_tip(self):
return self.span / self.AR / 2
```

expressions to compute default value, but can still be changed 

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

10 

**==> picture [50 x 162] intentionally omitted <==**

## **Input defaults – what to use, and when?** 

## • Benefits: 

- Users don’t need to specify all inputs, and still get a complete Part 

- Things that rarely change don’t need to be specified every time 

## • Dangers: 

- “Where does that number come from? I did not specify that!” 

- Accidentally treating input variables like constants 

## • Advice: 

- Provide defaults for values that rarely change: **`n_fuselages = Input(1)`** 

- Or for modifiable standard settings: **`Mach = Input(0.1) # incompressible by default`** 

- Defaults used for testing should be recognizably unrealistic! 

**==> picture [91 x 56] intentionally omitted <==**

- E.g. default chord = thickness = span …. =1m 

- …but even better not to use defaults this way 

**==> picture [145 x 52] intentionally omitted <==**

**----- Start of picture text -----**<br>
Make very obvious<br>that values are not<br>meant to be realistic<br>**----- End of picture text -----**<br>


**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

11 

**==> picture [50 x 162] intentionally omitted <==**

## **Attribute: embodies engineering rule / is an output** 

```
@Attribute(**kwargs)
def <name>(self):
<expression>*
return <expression>
```

```
class Wing(Base):
# ...
```

```
@Attribute
def c_tip(self):
return self.c_root *
self.taper
```

## See Exercise 3 code 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

12 

**==> picture [50 x 162] intentionally omitted <==**

## **Part: composition of child objects** 

```
@Part(**kwargs)
def <name>(self):
return <Class>(*args,
hidden=bool,
suppress=bool,
quantify=int,
pass_down=str,
map_down=str,
**kwargs)
```

**==> picture [91 x 56] intentionally omitted <==**

```
class Wing(Base):
# ...
```

```
class Airfoil(Base):
chord = Input()
```

**==> picture [258 x 83] intentionally omitted <==**

```
@Part
def airfoil:
return
```

`= Airfoil(chord self.c_root)` AE4204 Knowledge Based Engineering (KBE) 

**==> picture [93 x 50] intentionally omitted <==**

13 

**==> picture [50 x 162] intentionally omitted <==**

## **Single Part Example** 

```
class Wing(Base):
thickness= Input(0.2)
chord= Input(2)
```

```
@Part
defairfoil(self):
return Airfoil(thickness=self.thickness,
chord=self.chord)
class Airfoil(Base):
thickness= Input()
chord= Input()
```

**==> picture [52 x 203] intentionally omitted <==**

```
return Airfoil(pass_down=["thickness","chord"],
```

## You can use `pass_down` for conciseness 

**==> picture [91 x 56] intentionally omitted <==**

```
>>>wing = Wing()
>>>wing.airfoil.thickness
0.2
```

```
>>>wing.airfoil.chord
2
```

```
>>>wing.airfoil.hidden
False
```

```
>>>wing.chord = 3
>>>wing.airfoil.hidden
True
```

```
>>>wing.chord = 1e-4
>>>wing.airfoil
Undefined
```

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

14 

**==> picture [50 x 162] intentionally omitted <==**

## **Quantified Part Example** 

**==> picture [249 x 52] intentionally omitted <==**

**==> picture [831 x 168] intentionally omitted <==**

**==> picture [816 x 96] intentionally omitted <==**

```
=
label"root_airfoil" if child.index == 0else "other_airfoil")
```

## See also exercise 3: How is airfoil chord set? 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

15 

**==> picture [50 x 162] intentionally omitted <==**

## **EXE: the geometry-less aircraft** 

- Aircraft 

- Fuselage 

- Wing 

- Engines & nacelles 

## **EXE 4. See** **`Aircraft.py` on Brightspace** 

## Observe: 

- Class structure matches structure shown in parapy GUI 

- How does the volume calculation work? 

## Add: 

- Mass calculation (inspired by volume calculation) 

- Some additional component, e.g.: 

   - interiors in fuselage (use `quantify` ) 

   - High lift devices in wing 

   - 

… 

AE4204 Knowledge Based Engineering (KBE) 

16 

## **Para** _**Py**_ **Graphical User Interface (package: parapy.gui)** 

**==> picture [342 x 374] intentionally omitted <==**

**----- Start of picture text -----**<br>
Product<br>tree<br>Property Grid<br>**----- End of picture text -----**<br>


**==> picture [91 x 56] intentionally omitted <==**

Viewport 17 

AE4204 Knowledge Based Engineering (KBE) 

**==> picture [50 x 162] intentionally omitted <==**

**==> picture [91 x 56] intentionally omitted <==**

## **Para** _**Py**_ **GUI: Product Tree Context Menu** 

**==> picture [701 x 401] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

18 

**==> picture [50 x 162] intentionally omitted <==**

**==> picture [91 x 56] intentionally omitted <==**

## **Para** _**Py**_ **GUI: Product Tree Context Menu** 

**==> picture [588 x 374] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

19 

**==> picture [960 x 540] intentionally omitted <==**

**----- Start of picture text -----**<br>
Para Py  GUI: Property Grid<br>refresh<br>Level up object repr<br>To root evaluate all<br>expand /<br>Show<br>Show private  collapse<br>inherited slots<br>Input(), slots<br>@Input<br>@Attribute<br>double-click to<br>evaluate or inspect<br>@Part<br>AE4204 Knowledge Based Engineering (KBE) Path from root 20<br>**----- End of picture text -----**<br>


**==> picture [50 x 162] intentionally omitted <==**

## **Para** _**Py**_ **GUI: Viewport** 

**==> picture [481 x 339] intentionally omitted <==**

**==> picture [273 x 250] intentionally omitted <==**

**==> picture [683 x 55] intentionally omitted <==**

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

21 

**==> picture [50 x 162] intentionally omitted <==**

**==> picture [91 x 56] intentionally omitted <==**

## **Para** _**Py**_ **GUI: Viewport** 

**==> picture [731 x 392] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

22 



# --- END OF SOURCE: Tutorial 2 ParaPy classes and GUI.pdf ---



# ========================================================
# START OF SOURCE: Tutorial 4.pdf (Category: Parapy Documentation)
# ========================================================

**==> picture [50 x 162] intentionally omitted <==**

## **Knowledge Based Engineering (KBE) AE4202** 

**Tutorial 4 – ParaPy geometry (continued)** 

**Dr.ir. G. La Rocca** FPP 

- Boolean operations 

- Topology 

- Positioning by conditionals 

**==> picture [960 x 136] intentionally omitted <==**

**==> picture [960 x 57] intentionally omitted <==**

**==> picture [50 x 162] intentionally omitted <==**

## **Content** 

## 1. Boolean operations  **`exe_16_booleans.py`** 

## Reference document: **The (usual) ParaPy Tutorials booklet, Exercise 16** 

## 2. Notes on topology  **`topology.py`** 

3. Positioning objects using conditionals  **`exe_9_conditional_expressions.py`** Reference document: **Tutorial 4-Exe 9 on positioning** 

**==> picture [91 x 56] intentionally omitted <==**

**==> picture [93 x 50] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

2 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

Boolean operations allows generating complex geometries by uniting, intersecting, subtracting, etc. a set of starting primitives. 

In this exercise, your primitives are the ParaPy **`Box`** and **`Cone`** 

**==> picture [307 x 205] intentionally omitted <==**

Note that a `Cone*` instance is defined by 2 radii, 1 height and 1 angle 

`radius1` must be not null, but can be smaller than `radius2` 

`radius2` defaults to 0 and must be different than `radius1` (you do not get a cylinder when they are equal…) `height` is the distance between the 2 bases (or the basis and the apex) 

```
@Part
defcone(self):
return Cone(radius1=0.5,
radius2=0.2,
=
height1.5,
angle=math.pi* 3/2)
```

Check the use of angle to generate cone portions 

AE4204 Knowledge Based Engineering (KBE) 

3 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

CTRL+leftmouse click on `Cone` or `Box` to access their source code. (or any primitive) in Pycharm Note the definition of the input for the given class by means of `__initargs__` 

**==> picture [407 x 71] intentionally omitted <==**

These arguments need no keyword, so you can create an instance simply like this: 

`@Part` **`def`** `box(self):` The first input value will be automatically assigned to **`return`** `Box(1,1,1.1) width` , the second to `length` , etc. 

You can you can of course still be explicit on the argument names: 

**==> picture [37 x 56] intentionally omitted <==**

```
@Part
defbox(self):
return Box(height=1, length=1, width=1.1)
```

AE4204 Knowledge Based Engineering (KBE) 

4 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

**==> picture [636 x 343] intentionally omitted <==**

## `@Part` 

## **`def`** `box(self):` 

```
return Box(height=1, length=1, width=1.1,centered=True, color="green")
```

Check the effect `centered` on the positioning of the primitive 

AE4204 Knowledge Based Engineering (KBE) 

5 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

**==> picture [636 x 343] intentionally omitted <==**

## `@Part` 

## **`def`** `box(self):` 

```
return Box(height=1, length=1, width=1.1,centered=False, color="green")
```

Check the effect `centered` on the positioning of the primitive 

AE4204 Knowledge Based Engineering (KBE) 

6 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

Booleans operations in ParaPy require a `shape_in` and a `tool*` 

U 

```
@Part
deffused_solid(self):
return FusedSolid(shape_in=self.box, tool=self.cone)
```

```
@Part
defintersection_box_cone(self):
return CommonSolid(shape_in=self.box, tool=self.cone)
```

```
@Part
defbox_less_cone(self):
return SubtractedSolid(shape_in=self.box, tool=self.cone)
```

- 

**==> picture [133 x 106] intentionally omitted <==**

**==> picture [137 x 127] intentionally omitted <==**

**==> picture [136 x 124] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

7 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

**==> picture [186 x 123] intentionally omitted <==**

**----- Start of picture text -----**<br>
-<br>**----- End of picture text -----**<br>


```
@Part
defcone_less_box(self):
return SubtractedSolid(shape_in=self.cone, tool=self.box)
```

**==> picture [70 x 70] intentionally omitted <==**

**==> picture [70 x 70] intentionally omitted <==**

**==> picture [279 x 216] intentionally omitted <==**

**==> picture [306 x 236] intentionally omitted <==**

`cone` Reposition such not to pierce `box` and check the outcome 

## Operation fails when impossible to obtain one single solid 

AE4204 Knowledge Based Engineering (KBE) 

8 

**==> picture [50 x 162] intentionally omitted <==**

```
@Part
defpartitioned_solid(self):
return PartitionedSolid(solid_in=self.box,
tool=self.cone,
keep_tool=True)
```

## **Exe 16 on Boolean operations** 

**==> picture [663 x 358] intentionally omitted <==**

It generates a of **sequence** partitions, **including** those occurring in the `tool` 

ATT! Note that this Boolean requires a `solid_in` (rather than a `shape_in` ) 

AE4204 Knowledge Based Engineering (KBE) 

9 

**==> picture [50 x 162] intentionally omitted <==**

```
@Part
defpartitioned_solid(self):
return PartitionedSolid(solid_in=self.box,
tool=self.cone,
keep_tool=False)
```

## **Exe 16 on Boolean operations** 

**==> picture [663 x 357] intentionally omitted <==**

It generates a sequence of partitions (only those contained in the `solid_in` ) 

AE4204 Knowledge Based Engineering (KBE) 

10 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

`Plane` is a ParaPy class to define infinite* planar surfaces. 

It is useful, for example, to cut other geometry entities 

CTRL+rightmouse click, as usual, to find out how to define a plane, or check the documentation: 

**==> picture [526 x 206] intentionally omitted <==**

```
__initargs__ = ["reference", "normal", "binormal"]
```

The most common way to define a `Plane` instance is by providing a `reference` (i.e. **a point** ) and the `normal` to the plane (i.e. **a vector** )** 

AE4204 Knowledge Based Engineering (KBE) 

11 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

```
@Part
```

```
defcutting_plane(self):
```

```
return Plane(reference=self.box.cog, normal=VZ)  # that is how you define a plane
```

```
@Part
```

```
defhalf_space_solid(self):
```

```
return HalfSpaceSolid(self.cutting_plane, self.box.cog.translate('z', -0.2))
# the plane above is used to build an infinite solid. In this case: everything below cutting_plane
```

`HalfSpaceSolid` is a class to define an infinite solid, which is filling the space below or above a given surface (e.g. a `Plane` instance). 

As clear from its                                                               , a surface must be assigned to the `__initargs__ = [` **`"built_from"`** `,` **`"point"`** `]` input `built_from` , and a point (below or above) to `point` 

AE4204 Knowledge Based Engineering (KBE) 

12 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

Visualization of a planar instance of `HalfSpaceSolid` and its `build_from` surface (a plane in this case) 

Representation of a `HalfSpaceSolid` instance in the viewer 

Zoomed visualisation* of a `Plane` instance in the viewer 

AE4204 Knowledge Based Engineering (KBE) 

13 

**==> picture [50 x 162] intentionally omitted <==**

## **Exe 16 on Boolean operations** 

**==> picture [443 x 227] intentionally omitted <==**

```
@Part
```

```
defhalf_space_solid(self):
```

```
return HalfSpaceSolid(self.cutting_plane,
self.box.cog.translate('z', -0.2))
```

**==> picture [463 x 236] intentionally omitted <==**

```
@Part
defhalf_space_solid(self):
return HalfSpaceSolid(self.cutting_plane,
self.box.cog.translate('z', 0.2))
```

**==> picture [33 x 34] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

14 

**==> picture [50 x 162] intentionally omitted <==**

## **On geometry topology** 

- To operate at best with geometrical shapes it is convenient to familiarize with their topology. E.g. a Box is build of **Shells** , which include **Faces** , which have **Wires** , etc… (see UML class diagram) 

- With the **.dot** notation it is possible to access all topological elements and relative properties, for any 

**==> picture [468 x 321] intentionally omitted <==**

   - geometry primitive 

- Use **topology.py** to familiarize with topology concepts 

**==> picture [403 x 218] intentionally omitted <==**

```
topology.py
```

AE4204 Knowledge Based Engineering (KBE) 

15 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** **`exe_9_conditional_expressions.py`** 

**==> picture [521 x 321] intentionally omitted <==**

AE4204 Knowledge Based Engineering (KBE) 

16 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

**Assignment:** Generate a sequence of 10 boxes. Translate each next box in x-direction with 3 w.r.t. previous 

```
@Part
defboxes1(self):
```

```
return Box(quantify=self.n_boxes, height=1, width=1, length=1,
position=translate(
```

```
self.positionif child.index== 0 else child.previous.position,
'x', 3))
```

The distance to translate 

Position used as reference for each translation 

In this case it is evaluated using a conditional expression**: 

The first `Box` instance* use as reference position the one where the whole sequence `boxes1` is defined*** 

The direction along which to translate (the x axis of the given reference system) 

 Each child of the sequence is defined relatively to the previous. 

`Box` Each following instance uses as reference the position of the revious instance p 

If one child is moved, all the followings move as well (see next slide) 

AE4204 Knowledge Based Engineering (KBE) 

17 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

**Assignment:** Generate a sequence of 10 boxes. Translate each next box in x-direction with 3 w.r.t. previous XOY 

uses as reference the position of the previous 

Location = Point (3, 0, 0) Location = Point (6, 0, 0) Location = Point (14, 0, 0) Location = Point (17, 0, 0) Set the position of child[2] to Point(14, 0, 0), in place of Point(9, 0, 0) and observe that all following Location = Point (35, 0, 0) 

Set the position of child[2] to Point(14, 0, 0), in place of Point(9, 0, 0) and observe that all following children move accordingly 

Manually set 

AE4204 Knowledge Based Engineering (KBE) 

18 

**==> picture [50 x 162] intentionally omitted <==**

## **Conditional syntax** 

## **- Multi line** conditional syntax: 

```
if : @Part
conditional_1
defboxes1(self):
Expression1 return Box(quantify=self.n_boxes, height=1, width=1, length=1,
position=translate(
elifconditional_2:
self.positionif child.index== 0 else child.previous.position,
Expression2 'x', 3))
else:
Expression3
```

## **- One line** conditional syntax, also called a ternary operator: 

```
Expression1 ifconditional elseExpression2
```

ATT! Arguments definitions in Python only support one-line expressions. 

If you are more comfortable with the multi-line  syntax, use that to define attributes and use the result in the `@Part` definition. 

(This approach also enables more complex rules while keeping code more readable) 

AE4204 Knowledge Based Engineering (KBE) 

19 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

## **Variant previous assignment** 

```
@Part
defboxes1a(self):
```

```
return Box(quantify=self.n_boxes, height=1, width=1, length=1, color="red",
position=translate(
```

```
self.position,
'x'
,
```

The direction along which to translate (the x axis of the global reference system) The distance to translate 

- `(child.index + 1) * 3,` 

```
'y', 3))
```

## Position used as reference for **all** translations 

In this case it is the one where the whole sequence `boxes1a` is defined*** 

- **Each child of the sequence is defined in the same reference system! (next slide)** 

AE4204 Knowledge Based Engineering (KBE) 

20 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

**Assignment:** Generate a sequence of 10 boxes. Translate each next box in x-direction with 3 w.r.t. previous 

XOY uses as reference XOY Location = Point (3, 3, 0) Location = Point (6, 3, 0) Location = Point (14, 3, 0) Location = Point (18, 3, 0) Set the position of child[2] to Point(14, 3, 0), in place of Point(9, Location = Point (30, 3, 0) 3, 0) and observe that all the other children are not affected 

Manually set 

AE4204 Knowledge Based Engineering (KBE) 

21 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

**Assignment:** Anchor first box at `self.position` . Then, translate each next box according to their index: - even index: translate in 'x' direction by 4 

- odd index : translate in 'y' direction by 2 

```
@Part
defboxes2(self):
```

```
return Box(quantify=self.n_boxes, width=1, length=1, height=1, color='green',
position=translate(
```

first child anchored at the location of `self.position` 

```
)
```

```
self.positionif child.index== 0 else child.previous.position,
'x' if child.index% 2 == 0 else 'y',
```

```
0 if child.index== 0 else 4 if child.index% 2 == 0 else 2)
```

```
Expression1 ifconditional elseExpression2
```

## **- Nested one line** conditional syntax, where Expression2 has also one-line conditional syntax 

AE4204 Knowledge Based Engineering (KBE) 

22 

**==> picture [50 x 162] intentionally omitted <==**

## **Object positioning with conditionals** 

## **Variant on previous assignment to avoid complex one-line conditionals inside the return** 

**==> picture [589 x 246] intentionally omitted <==**

Use an `@Attribute` to evaluate the list of positions and… 

```
@Part
defboxes2a(self):
```

…keep the return expression uncluttered 

```
return Box(quantify=self.n_boxes, width=1, length=1, height=1,
position=self.positions2[child.index])
```

AE4204 Knowledge Based Engineering (KBE) 

23 



# --- END OF SOURCE: Tutorial 4.pdf ---

