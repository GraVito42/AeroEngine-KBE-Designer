# KNOWLEDGE BASE: MULTALL DOCUMENTATION

This document contains the merged content of the following source files:
- General-description.pdf
- Inverse-design mode .pdf
- lookup-table.pdf
- Meangen-differences.pdf
- meangen-instructions.pdf
- Multall Tutorial 2020.pdf
- Multall Tutorial 2021 (including TecPlot).pdf
- Multall Tutorial 2023.pdf
- new-readin-input-data-20.9 .pdf
- PostPy_documentation.pdf
- README.pdf
- Stagen-18.1-instructions.pdf
- updates.pdf

---



# ========================================================
# START OF SOURCE: General-description.pdf (Category: Multall Documentation)
# ========================================================

1 

# MULTISTAGE TURBOMACHINERY FLOW CALCULATION PROGRAM MULTALL_OPEN 

Written for MULTALL_OPEN. February 2017 

## Updated for MULTALL-OPEN-20.9.  November 2020. 

## **DEVELOPMENT HISTORY** 

Program **MULTALL** is a 3D multistage turbomachinery flow calculation program developed by Prof John Denton at the Whittle Lab, Cambridge, UK, over many years. In fact its origins go back to when the author was working at the CEGB Marchwood Engineering Labs around 1973. The program is based on the finite volume time marching method. The original version in the early 1970’s was inviscid and for a single blade row. It used the “opposed difference” numerical scheme and an overlapping grid system. It rapidly became popular because it was much faster than previous 3D methods.  The extension to multiple blade rows, using the mixing plane model, took place around 1978. Around 1980 the grid was changed to use cell corner storage with no overlapping, as still used today. Around the same time multigrid was added and spatially varied time steps were used, giving a significant speed up in run times. The multigrid differs from the conventional model in that it is simpler, faster and arbitrary block sizes can be used.  Several different versions were developed around this time to include splitter blades, part-span shrouds, cooling flows, bleed flows, etc. 

In the mid 1980’s simple models of viscous effects were added. The first of these simply added the displacement thickness of a very simply calculated boundary layer to the blade shape. Then the body force model of viscous effects was developed, with the body forces initially calculated by a thin shear layer approximation to the Navier-Stokes equations. The model used a mixing length turbulence model and wall functions for the surface shear stresses. The body force model itself is not an approximation and has the major advantage that the body forces only need to be updated every few (typically 5 or 10) time steps making it much faster than conventional N-S methods. The original simple model, subroutine LOSS, proved remarkably accurate and is still widely used today. 

The solution algorithm was changed to use the “scree” scheme around 2000, this reduced the level of numerical viscosity and greatly helped with the calculation of low Mach number flows and reversed flows. Cooling and bleed flows and an allowance for surface roughness were incorporated into the basic program rather than into separate versions. An allowance for real gas flows was also included in the basic program and a separate version, MSTEAM, not described here, with steam properties was developed.  Several improvements to the mixing plane model were also made around this time. Two different viscous models were added around 2010, the Spalart-Almaras model in subroutine SPAL_LOSS and an improved mixing length model in subroutine NEW_LOSS. 

Around 2013 option to use an improved version of the “scree” scheme, the “SSS” scheme was introduced, allowing larger CFL numbers but being less robust than the basic “scree” scheme. In most 

2 

cases the basic “scree” scheme is still preferred. An option to perform quasi-3D blade-to-blade calculations on a stream surface using only a single cell in the spanwise direction was introduced in 2015 and a throughflow methiod, using a single cell in the pitchwise direction in 2016. 

An option to run at very low Mach numbers, or even with fully incompressible flow was first added in the 1990’s and was updated in 2016. 

The current version  MULTALL_OPEN  has been considerably tidied up from the previous version, MULTALL_15.2, but the only new feature that has been added is the ability to perform an axisymmetric throughflow calculation using only a single cell in the pitchwise direction. The input data has been considerably modified to try to make it more systematic and this makes it no longer compatible with data sets for previous versions. However, the option to use a data set closely compatible with MULTALL_15.2 set has been left in the code so that previous users can continue to use their old data sets with minimum modification. A program named CONVERT.F, to convert MULTALL_15 data sets to MULTALL_OPEN data sets with NEW_READIN  format is available. 

An inverse design option for quasi-3D blade to blade flows was introduced in version 20.6. This enables blades to be designed with a specified surface pressure distribution.  A separate detailed description for this version, entitled  “inverse-design-mode.docx”  is provided in this folder. 

An option to obtain the fluid properties from a “look-up-table” as an alternative to the perfect gas model was introduced in version 20.9. This can be used for any fluid for which data is available but only tables for steam are provided.  This option is described in this document. 

The program is for steady flow only. Unsteady flow can be calculated by the author’s other programs UNSTREST and TBLOCK which are not freely available. 

## **OVERVIEW** 

MULTALL is a three dimensional flow calculation program which has been specifically developed for turbomachinery. The program is written in standard Fortran77 and should run on any computer with a Fortran compiler. The only non-standard feature is the call to the timing routine, MCLOCK, which is specific to the gfortran  and g77 Linux compilers. This should be removed or replaced by an equivalent call if using other compilers. 

The program can be used for axial, mixed or radial flow turbomachinery with no limitation, apart from computer storage requirements, on the number of blade rows calculated. However, it only calculates the main flow path so the annulus boundaries have to be surfaces of revolution and split flow paths, e.g. splitter blades or part span shrouds, cannot be included. The interface between blade rows is modeled using a highly developed mixing plane model. 

The program is designed to be relatively simple and is also relatively fast with run times of order 15 minutes per blade row on a single processor. Tip leakage flow can be predicted using the pinched tip model and shrouded blade leakages using a source-sink model. Although the basic scheme works down to Mach numbers of order 0.15, low Mach number and incompressible flow options are provided. A source-sink model may also be used to predict cooling flows and bleed flows. Turbulence modeling is 

3 

either by a thin shear layer mixing length model, a full Navier-Stokes mixing length model or the Spalart-Almaras model. Boundary layer transition may be either specified or modeled and the effects of surface roughness can be predicted. A limited redesign of the blade sections can be performed within the program. 

Version 19.2  has one major addition, that is an option for an improved exit boundary condition. This is based on a one-dimensional method of characteristics. It is felt to give a more “non-reflecting” condition which is particularly desirable when shock waves intersect the downstream boundary. The previous method is retained as an option. The other changes in version 19.2 involve only minor “bugs” and tidying up. 

The new exit boundary condition is only available if using “NEW_READIN” data input format. 

Version 20.6 includes an option to perform inverse design of blades on a Q3D blade-to-blade stream surface. A detailed description of this version in given in a separate document entitled “inverse-designmode.docx” in this folder. 

Version 20.9 includes an option to obtain the fluid properties from a “look-up-table”  rather than from a perfect or semi-perfect gas assumption. In principle this can be used with any fluid for which tabulated properties are available but at present tables are only provided for steam properties.  The data for most fluids can be obtained from the  COOLPROP system of programs and a program for generating the required table is provided. This must be linked to the COOLPROP system. This is described on page 17 of this document. 

Detailed instructions for compiling and running the program are given at the end of this document. 

4 

## **SOLUTION ALGORITHM** 

MULTALL uses the “scree” algorithm instead of the previous "Opposed Difference Scheme" which was used up to MULTIP75. The “scree” scheme is an extremely simple method that is completely second order accurate in space. The primary flow variables F (where  F = ρ, ρE, ρVx, ρVr, or ρrVt) are updated on every timestep using 

**==> picture [193 x 33] intentionally omitted <==**

where  n is the time step level. This may be thought of as an extrapolation of the rate of change to the end of the time step. This involves only a single flux evaluation per time step and so is much faster than multi-step schemes. The scheme is only first order accurate in time but this is not important for steady calculations. The “scree” scheme can be used with much lower values of artificial viscosity (smoothing) than most other algorithms and does not need any special treatment or loss of accuracy to handle reversed axial velocities. The scheme is also better than most others at very low Mach numbers and solutions can be obtained for effectively incompressible flow at Mach numbers of order 0.15. 

The maximum stable timestep with the “scree” scheme is that giving a CFL number around 0.5, but as a safety factor it is more usual to set CFL = 0.4. Compared to all previous versions of this code he CPU time per point per timestep is only slightly reduced but the number of timesteps required for convergence is generally significantly reduced. Convergence is generally much more continuous than with the opposed difference scheme and, once over the initial transients, the graph of log(residual) vs time step number soon becomes a straight line. 

The “super_scree” algorithm, available in TBLOCK, never worked well on real problems, although it works well on a uniform grid. It was found to be sensitive to the multigrid on non-uniform grids. It was then realised that the “super_scree” algorithm could be approximated without using the additional storage for the derivatives at the N-2 timestep by setting 

**==> picture [205 x 34] intentionally omitted <==**

Where Δ  is the change applied, Δt is the time step, Vol the cell volume and  Rn is the residual at step  n. F1, F2  and F3  are constants. 

This makes the second term into a geometric series of past residuals and to make the sum of all coefficients = 1.0, so that its time steps are comparable to the “scree” scheme, we must set 

**==> picture [158 x 16] intentionally omitted <==**

It is found that the combination 

5 

**==> picture [187 x 13] intentionally omitted <==**

is close to optimum and allows CFL numbers up to about 0.7 compared to 0.4 for the “scree” scheme. Higher values, up to 0.9, can sometimes be used. The combination F2/(1-F3) is referred to as the effective value of F2,  F2eff  ,  and it is this value that must be input in the data file. i.e.  the typical input value of F2eff  = -1.0 . This is called the  “SSS” (Simple Super Scree) scheme. 

It was also found that the CFL number could be increased slightly further by the use of residual averaging, i.e. smoothing the values of  Rn . A smoothing subroutine,  SMOOTH_RESID,  is included to perform this, although its use is optional. A single smoothing with smoothing factor 0.4 allows a small increase in CFL at the expense of about 7.5% increase in run time per step. However, a major advantage is an increase in robustness. The program no longer fails when the stable CFL number is exceeded. Instead the residuals at the unstable points oscillate at high frequency about a steady average. Although the residuals may not decrease to low levels the resulting solutions appear identical to fully converged ones. CFL values up to 0.9 can sometimes be used in such cases but it is safer to choose 0.7 as a standard value. 

## **GRID** 

The program uses a standard "H" grid composed of pitchwise (J and K constant, I varies) grid lines, streamwise (I and K constant, J varies) grid lines and quasi-orthogonal (I and J = constant, K varies) grid lines. The simple H grid greatly simplifies grid generation, the application of the periodic boundary conditions and the modeling of the mixing planes. It inevitably leads to highly sheared cells for staggered blade rows but experience is that the numerical errors associated with this (as judged by the entropy change in inviscid flow) are negligible when "viscous" grids with more than about 30 points across the pitch and span, and with close meridional spacing around the leading edge, are used. 

All variables are stored at cell corners, as illustrated below, which the author believes to be simpler and more accurate than cell centre storage. The cell indexing system is also illustrated in the Figure below. The cell numbered (I,J,K) has the grid point I,J,K at its corner with the largest J value, lowest I and lowest K values. 

A typical number of grid points for an inviscid calculation would be  IM = KM = 28, JM = 75, with fairly uniform spacing of the points in each direction, except for the J spacing being considerably reduced around the leading edge. For a viscous calculation a typical number would be IM = KM = 49, JM =150, with highly non-uniform spacing in the pitchwise and spanwise directions, a typical grid stretching factor in these directions would be 1:20. 

**==> picture [255 x 166] intentionally omitted <==**

**----- Start of picture text -----**<br>
K=KM J=JM<br>K Grid<br>Direction J Grid<br>R<br>Direction<br>J=1<br>J=JLE<br>Stream Surface<br>m<br>J=JTE<br>X<br>K=1<br>**----- End of picture text -----**<br>


COORDINATES IN THE MERIDIONAL VIEW 

6 

**==> picture [363 x 339] intentionally omitted <==**

**----- Start of picture text -----**<br>
I Grid<br>I=IM<br>Direction<br>J=JLE<br>Theta Direction<br>J=1<br>I=1<br>J=JTE<br>m Direction<br>COORDINATES IN THE<br>J Grid Direction<br>BLADE TO BLADE VIEW<br>J=JM<br>**----- End of picture text -----**<br>


**==> picture [408 x 274] intentionally omitted <==**

**----- Start of picture text -----**<br>
Grid point<br>Grid point (I+1,J,K+1)<br>(I+1,J-1,K+1)<br>Grid point<br>(I,J,K+1 )<br>Grid point<br>(I,J-1,K+1)<br>CELL (I,J,K)<br>Grid point<br>(I+1,J,K)<br>Grid point<br>Grid point<br>(I,J,K)<br>(I,J-1,K)<br>K(Spanwise)<br>CELL INDEXING SYSTEM I (Pitchwise)<br>THE CELL ILLUSTRATED<br>IS REFERENCED AS CELL<br>J<br>(I,J,K) Meridional)<br>**----- End of picture text -----**<br>


7 

**==> picture [380 x 253] intentionally omitted <==**

Blade-to-blade view of the grid on a streamwise surface. Coarse grid shown. 

**==> picture [326 x 238] intentionally omitted <==**

Meridional view of the grid. Coarse grid shown. 

8 

**==> picture [294 x 241] intentionally omitted <==**

Quasi-orthogonal view of the grid. Coarse grid shown. 

The grid lines should be closely spaced around the leading edge where flow properties change very rapidly, but experience shows that it is best to use a relatively coarse grid spacing, with a cusp, at the trailing edge. This is because a fine grid around the trailing edge usually gives unrealistic negative loading at the trailing edge. A cusp at the trailing edge is the standard option in this program but the latest versions allow a body force field and a fine grid to be used instead of a cusp to force the flow to separate at the trailing edge. 

## **MULTIGRID** 

The most important factor in accelerating the convergence of the calculation is the use of multigrid. Three levels of multigrid are usually used and, unlike most other methods, the block sizes are not limited to simply doubling of the number of cells in each direction. In fact the size of the blocks may be chosen arbitrarily by the user but experience is that blocks of 3x3x3 cells for the lowest level and 9x9x9 cells for the middle level are often the optimum. It is best, but not essential, if there are a whole number of blocks across the span and pitch of the blade passage. The third level of multigrid is a onedimensional calculation in which the blocks extend across the whole pitch and whole span with a fixed number of 4 blocks per blade row in the streamwise direction. The gives very rapid transfer of information from inlet to outlet of the whole flow field and so greatly speeds up convergence of multistage calculations. 

The number of time steps for convergence depends greatly on the problem, particularly on the number of stages and on the uniformity of the grid, but it is typically in the range 2000 – 5000. The more the number of blade rows calculated and the more closely spaced the grid points the larger is the number of 

9 

steps required for convergence. The convergence limit set in the data is the average percentage change in meridional velocity per time step. A value of 0.005 is usual but lower values can be used if required. The calculation will not converge unless the maximum continuity error, i.e. the maximum difference between the local mass flow rate and the inlet flow rate, is less than 1%. 

## **NEGATIVE FEEDBACK** 

This is a very simple but effective means of increasing the robustness of a code. It could be applied to most explicit CFD codes. The idea is to limit the rates of change of the flow properties at grid points where the calculated rates of change are greatest. 

After summing the fluxes and multiplying by the local time step for all cells, the resulting rates of change, Δcalc, are obtained. The absolute magnitudes of the rates of change are then averaged to find, Δavg, for the whole flow field. The rates of change of all cells are then changed by 

**==> picture [275 x 37] intentionally omitted <==**

DAMP is an input variable which controls the amount of negative feedback. Cells where the calculated change is much less than (DAMP x Δavg) will scarcely be changed but cells where the calculated change is comparable to or greater than (DAMP  x Δavg) will have their changes reduced. This acts as a powerful stabilising influence on cells which might be unstable due to locally very high Mach numbers. Such local instabilities often occur during an initial transient when starting from a crude initial guess of the flow and would otherwise require the whole calculation to be run with a lower CFL number and/or higher smoothing. Typical values of DAMP are 10 – 25, but lower values may be used for difficult cases. If DAMP is set greater than 100 it is not used. The value of DAMP should have no effect on the final solution. 

## **MIXING PLANE MODEL** 

Development of a satisfactory mixing plane model is an extremely difficult task. The objective is to allow the flow to mix out instantaneously at a plane between the blade rows, rather than gradually within the downstream blade row, whilst maintaining the mixing loss at a similar value. The mixing plane must conserve the pitchwise averaged fluxes of mass, momentum and energy but it must not impose pitchwise uniform conditions on the flow. In general the static pressure will rise and the entropy increase across the mixing plane to simulate the real mixing process. The mixing plane treatment has evolved over many years and has been changed and improved compared to the original very simple model. A detailed description of the current model is given in the note 17. The quasiorthogonal grid lines at J = JMIX and J =  JMIX +1 must be coincident in the meridional view, i.e. they must have the same x and r coordinates. This is done automatically by subroutines GRIDUP and GRIDOWN if the options ISHIFT = 2 , 3 or 4 are used. Use of this option is very strongly recommended. 

10 

## **VISCOUS MODELLING** 

As in all recent versions of the code viscous terms are included via body forces and source terms. The use of body forces to solve the Navier-Stokes equations is not an approximation and can be made as exact as any other method. The advantage of using the body force model is that the viscous terms need not be evaluated every time step, typically they are evaluated only every 5 steps leading to a very significant saving in CPU time. The code can be run as an inviscid calculation by setting ILOS = 0. 

The wall shear stresses are obtained from wall functions. The usual model used assumes that the second grid point from the wall is either in the log-law region of a turbulent boundary layer, or in a laminar boundary layer. In this model the wall shear stress is obtained from a curve fit to the log law for equilibrium boundary layers. This gives a very good fit to the shear stress obtained from the standard log law over the range of Yplus from 25  to 1000. This model is used if the variable YPLUSWALL is less than 5. A different wall function is used if YPLUSWALL is greater than 5 and this uses an assumption that the first grid point is in the laminar sub layer at the specified value of YPLUS. This simplifies the calculation of skin friction but does not allow the skin friction to change with Reynolds number and so the chosen value of YPLUSWALL must be adjusted manually to allow for different Reynolds numbers. Hence the first (original) method is generally preferred. 

A further option to use the wall functions suggested by Shih et al in NASA/TM-1999-209398 is available in version 17.5. These consist of two terms, a velocity based term and a pressure gradient based term.  Only the velocity based term is used if YPLUSWALL is set in the range  -10.0 to zero. This gives results very similar to the original wall functions. Both terms are used if YPLUSWALL is set below -10.0 , there is little experience of using this term as yet but is does not seem to make much difference for moderate pressure gradients. 

Boundary layer transition can be specified at any point on any surface or can be predicted very approximately by the simple transition model suggested by Baldwin and Lomax. 

The body forces were originally obtained from a thin shear layer approximation to the Navier-Stokes equations. The “thin shear layer” model is an approximation which assumes that viscous normal stresses and viscous stresses on the quasi-orthogonal faces of the elements can be neglected. Experience shows that this is not a severe limitation for turbomachinery flows. The turbulent viscosity in the original model is calculated using the mixing length approach. The mixing length is taken to vary linearly with distance from a wall up to a specified limit. This limit is input as data as a fraction of the local blade pitch and can be different on each blade surface and on each end wall, typically a limit = 0.03 of the local blade pitch is used. Lower values will give lower turbulent viscosity at the edge of the boundary layer, and hence less loss, and vice-versa. This model is still available in the code as subroutine LOSS, it is the fastest and most robust of the loss models. 

Earlier versions of the program omitted shear work and internal heat flows because they may be shown to cancel in a flow with a pitchwise uniform stagnation temperature and a Prandtl number of unity. However, for cooling flows that model is not realistic and these terms are now included in all recent versions.  All surfaces are, however, assumed to be adiabatic so heat transfer to or from solid to the gas cannot be calculated. 

11 

All recent version of the code include new loss routines NEW_LOSS and SPAL_LOSS. NEW_LOSS is an improved mixing length model, SPAL_LOSS is the well-known Spalart-Allmaras (SA) turbulence model. Both of these solve the full Navier-Stokes equations. They use exactly the same wall functions as in the original LOSS method. 

In NEW_LOSS the local mixing length limit is calculated from the distance of the mid-span and midpitch point to the nearest solid surface.  It is therefore roughly proportional to the local blade passage width. This length is then multiplied by a scaling factor which in input as data. The scaling factor is input for each blade row at blade row inlet (mixing plane), leading edge, trailing edge and exit (mixing plane) and is taken to vary linearly with meridional distance between these points. The value of the scaling factor should be similar to the mixing length limit used in the original LOSS routine but experience is that is needs to be slightly larger, say 0.04 instead of 0.03. The mixing length is taken as the lower of this value and the local perpendicular distance to the nearest wall. Note that, unlike in subroutine LOSS, the mixing length limit cannot be varied between the different blade surfaces or the different endwall surfaces, it can only be varied with meridional distance. The turbulent viscosity is calculated from the square of the mixing length x the local absolute vorticity x local density. Free stream turbulence may be included by inputting the ratio of the free stream turbulent viscosity to laminar viscosity in every blade row. 

SPAL_LOSS is the Spalart-Almaras turbulence model. In this an additional convection equation is solved for the transformed turbulent viscosity. This uses about 20% more CPU time than the original LOSS method. However, the very complex source term used in the SA model is only calculated every 5-10 time steps and so does not use too much CPU time. In addition to the 4 source terms used in the basic SA model an additional source term has been added. This forces the turbulent viscosity towards the value obtained from NEW_LOSS model. Each of the source terms is multiplied by a scaling factor, which is input as data, and so the latter term would usually be turned off (scaled by zero) to obtain the basic SA model. By including the additional source term either hybrid mixing length-SA models or a modified mixing length model with convection of the turbulent viscosity, may be obtained. Experience is that the basic S-A model tends to underestimate the loss in turbomachinery and this may be corrected by increasing the main source term, FAC_ST0, setting this to 1.5 seems to give better results than the standard value of 1.0. 

Version 17.5 includes an option to increase the main source term, FAC_ST0, in the SA model as suggested by Lee et al in ASME paper GT2017-63245. The increase consists of two terms, one increasing the source term due to streamwise vorticity (helicity) and the second increasing it due to adverse pressure gradients. These are used if the values of FAC_VORT  and FAC_PGRAD in CARD 30  and set to be greater than zero. Lee et al suggest values of FAC_VORT = 0.9191  and FAC_PGRAD = 0.6565 but the values used are determined by the values input. There is little experience yet of using this option but it certainly does increase the turbulent viscosity in the boundary layers and should be useful in extending the operating range of compressors near their stall point. 

With any turbulence model a question arises of how to model the transfer the turbulent viscosity across a mixing plane. This is modeled by pitchwise averaging the values of turbulent viscosity upstream of the mixing plane and passing a fraction of this average across the mixing plane as a pitchwise uniform variation to the next blade row. The fraction transferred in input as data for each blade row. It is difficult to know what is the correct fraction to transfer but a value around 0.5 seems appropriate. 

12 

The laminar viscosity may either be input directly as the dynamic viscosity or it can be calculated within the program by inputting the Reynolds number of the first blade row. The laminar viscosity is usually taken to be constant but if the input value of Reynolds number, Re, is negative then the viscosity at 288K is the (absolute value of Re) x 10[-5  ] and it is then automatically scaled by a power law to allow for its variation with local temperature. e.g. for air the viscosity would be input as -1.9 and it would be automatically changed with temperature.  This option is especially useful for multistage high speed machines where the temperature , and hence viscosity, varies significantly. 

There is an option to allow for the increased skin friction due to surface roughness. Different levels of roughness can be specified on each surface and the wall functions are modified to allow for the roughness. 

Boundary layer transition can be specified at a fixed “J” value in all 3 loss routines and the “J” value may be different on each surface. In LOSS and NEW_LOSS it is also possible to use a simple transition model, which says that the flow becomes turbulent when the maximum ratio of turbulent to laminar viscosity through the boundary layer exceeds an input limit. This is the model originally suggested by Baldwin & Lomax. This limit, FTRANS is typically 14. To obtain fully turbulent boundary layer the value of FTRANS should be very low and to obtain fully laminar ones it should be very high, say 10000 .  The use of FTRANS  is not possible with the SPAL_LOSS model, but this model automatically makes the turbulent viscosity low in laminar regions. 

If very fine grids are used near to a solid boundary, i.e. a large number of points with a high expansion ratio, then it is possible that there may be several grid points within the laminar sub layer. The wall functions used originally only allowed the first grid point from the wall to be in the sub layer and calculated a turbulent viscosity for all other points. However, recent versions have an option to reduce the turbulent viscosity for grid points within the laminar sub layer and buffer layer, typically up to yplus = 25. This only has any effect if more than 2 points are within these layers, which is only likely to occur when very fine grids are used. This has little effect on the SA model but makes solutions with LOSS10 or NEW_LOSS more grid independent. 

## **TIP LEAKAGE FLOWS** 

Tip leakage for plain tip clearances is calculated using the "pinched tip model" in which the blade is thinned towards the tip and periodicity is applied across the tip gap where the blade thickness is set to zero. This model may be used for stator hub clearances or rotor tip clearances. The model seems to give very realistic results, although, for thick blades, the actual tip gap calculated may need to be less than the physical gap to allow for the contraction of the leakage jet. A reduction in the tip gap to about 0.6 of the physical gap is recommended in such cases. The tip clearance is specified as a fraction of the local span at the blade leading and trailing edges and varies linearly between them. The number of grid cells within the gap is specified in the data and the grid is automatically adjusted to fit the gap. Typically 3 to 5 cells within the tip gap would be sufficient. 

13 

## **SHROUD LEAKAGE FLOWS** 

MULTALL also contains a shroud leakage model that models the leakage flow and loss for shrouded turbine rotor blades or compressor stator blades. The leakage mass flow is estimated from the seal clearance, the number of seals, the upstream stagnation pressure and the downstream static pressure and is bled off from the main flow. The change of angular momentum of the leakage flow due to friction on the shroud and casing is estimated using input values of the skin friction coefficient. The work done on the shroud by the leakage flow is also calculated. The leakage flow is then injected into the main flow downstream of the blade row and the conservation equations determine the mixing loss. Either hub or tip leakage can be calculated in this way and the flow may be from upstream of the blade row to downstream, as in turbine rotor blades, or from downstream to upstream as in compressor stator blades. 

## **GENERATION OF MODIFIED GRIDS** 

The number of grid points in the pitchwise and spanwise directions must be the same for all blade rows and are specified by IM  and KM in the input data. The grid spacing in the pitchwise (I) and spanwise (K) directions can be easily changed by specifying FP(I)  and FR(K) in the input data. The spacings can etiher be input directly or generated by the program from input values of the expansion ratio and maximum grid expansion. The spacing in the streamwise (J or meridional direction) can also be changed using subroutine NEWGRID. This enables a new grid with a different number of  “J” grid points to be generated from the input data. It is useful whenever more grid points are needed or the grid needs to be refined locally. Either the _relative_ meridional spacing of all the new grid points can be input as data, or the _relative_ spacing at just a few points can be input as a function of the meridional distance, the program then interpolates in these few points to obtain all the new grid spacings and hence the new grid points. 

The grids input in the data set may overlap in the meridional direction and they need not be contiguous at the mixing planes. If ISHIFT = 2, 3 or 4 is specified then the grids are automatically made contiguous at the mixing planes with the grid spacings made into a geometric series away from the trailing edge and leading edge. If too many points are used between the trailing edge or the leading edge and the mixing plane the geometric series may produce very close spacings at the mixing plane and this may cause instability. 

## **CUSP GENERATION** 

Although it is not essential to use cusps at the blade leading and trailing edges it is strongly recommended that a cusp is used at a thick trailing edge. If a cusp is used then the grid spacing should not be reduced at the trailing edge but should be made similar to that on the rear of the blade. The trailing edge cusp applies a blockage to the flow but carries no tangential load and hence does no work. It allows the flow to separate from the blade surfaces at well defined points without it starting to turn around the trailing edge, which would cause it to generate locally low pressures on the near trailing edge points. A flexible method of cusp generation at blade trailing edges is included in the program. The shape and length of the cusp can be chosen and also part of the cusp can be treated as a part of the blade so that it carries load. Cusps are not necessary at the blade leading edge as long as sufficient grid points are used to define the flow around the leading edge circle. A very fine grid is needed to achieve 

14 

this, typically about 6 points on the leading edge circle, this number may be reduced by using a cusp at the leading edge but this is not usual. 

The program also includes an option force the flow at the trailing edge to separate by a body force. This allows a fine grid to be used around a thick trailing edge without the solution generating unrealistic reverse loading at the trailing edge. See Note 16. However, this option is not often used. 

## **EXIT FLOW THROTTLING** 

An option to model a “perforated plate” type of downstream boundary condition is included. This is useful when there is a separated flow at the downstream boundary so that the meridional velocity is negative and the standard boundary condition becomes ill conditioned. The flow is made more uniform at the downstream boundary by simulating the presence of a flow resistance, such as a gauze or a perforated plate, at the boundary. This effectively adds a pressure drop equal to PLATE_LOSS x 0.5*ρ*(Vm[2] - Vmmid2) at the exit. Thus it should not change the average exit static pressure but it does force the flow to become more uniform at the exit boundary.  A typical value of PLATE_LOSS is about 2. If PLATE_LOSS  is set to zero then the option is not used. 

An alternative treatment for problems at the exit boundary is to increase the smoothing of the flow for points close to it. The flow may be given an extra smoothing, using a smoothing factor SFEXIT, which is applied over NSFEXIT grid points upstream from the downstream boundary. Typical values might be SFEXIT = 0.05, NSFEXIT = 10 . This option usually works well and is generally preferred to the simulated perforated plate model, but should only be used if the exit boundary is well downstream of the last blade row. 

It is also possible to use a throttle boundary condition to vary the exit static pressure with the exit mass flow rate. This gives improved stability near to the stall point for compressors. This option is used if THROTTLE_EXIT is greater than zero. The exit static pressure is made to vary parabolically with the exit mass flow according to: 

## Pexit = THROTTLE_PRES * (mexit/THROTTLE_MAS)[2 ] 

Where THROTTLE_PRES is the required exit pressure in N/m[2] and THROTTLE_MAS is the expected exit mass flow rate in Kg/sec. Changes in exit pressure are relaxed by RFTHROTL which, together with THROTTLE_PRES and THROTTLE_MAS, is input as data if THROTTLE_EXIT is non zero.  Increasing the value of THROTTLE_PRES will increase the back pressure and move a compressor towards stall. However, forcing the exit flow to lie on a parabolic pressure:mass flow characteristic through the specified point allows a closer approach to the true stall point than was previously possible. Use of this option is recommended for all compressor calculations near their stall point. THROTTLE_EXIT must be set to zero to prevent the use of this option. 

15 

## **BLADE AND ENDWALL COOLING FLOWS** 

Cooling flows can be added at any point on the blade and endwall surfaces. The flow is added through a series of  "patches" whose I,J,K boundaries are specified in the input data. If the "mixing plane" falls within a region where coolant is being added then two separate patches, one upstream and one downstream of the "mixing plane" must be used. The coolant mass flow, stagnation temperature, stagnation pressure, ejection Mach number and flow directions must be specified for each patch. Note that the exit relative Mach number of the coolant flow is specified and is not calculated from the local static and stagnation pressures. If it is required to model individual cooling holes then each patch may be one grid cell in size, but this requires a great deal of input data and it is more usual to specify a single patch to cover multiple cooling flows. The overall total-to-total efficiency is calculated and printed out, allowing for the potential work of all the cooling flows. However, the polytropic efficiencies, which are also printed out, relate the mass averaged inlet and outlet flow conditions and are not meaningful when cooling flows are added. 

The cooling flow temperature and pressure are input at the point where the flow is fed into the (possibly rotating) disc together with its angular momentum at that point. The pumping work done on the coolant by a rotating blade, and its consequent stagnation pressure and temperature at the point of ejection, is calculated by the program. 

## **BLEED FLOWS** 

Flow can be bled from the machine (as is common in steam turbines for feed heating or in gas turbine compressors for turbine cooling) at any point on the blade surfaces or on the hub and casing. As with coolant flows the flow is bled off from a "patch" whose I,J,K boundaries must be specified by the user. However, the bled flow is always assumed to have the flow properties, e.g. enthalpy and entropy, at the point where it is bled off, and so they cannot be specified by the user. The machine power output/input is calculated allowing for the bled flows but the efficiencies which are printed out are defined by using the inlet and outlet states of the flow remaining in the machine and do not allow for the bleed flows. 

## **LOW SPEED FLOWS** 

The basic program works remarkably well at low Mach numbers and will usually converge if the average Mach number is greater than about 0.15, which gives effectively incompressible flow. However, convergence becomes slower at low Mach numbers and so the program has been extended to use the artificial compressibility method to work with very low speed or incompressible flows. 

The method works be inputting an artificial speed of sound, Vsnd and calculating pressure changes directly from changes in an artificial density, Rosub, using 

**==> picture [119 x 17] intentionally omitted <==**

The change ΔRosub in the artificial density is obtained from the continuity equation in the usual way. The change in pressure is then calculated using 

16 

**==> picture [170 x 18] intentionally omitted <==**

Pref   and  Roref  are usually taken to be the inlet stagnation pressure and density. 

The true density, which changes only slightly in low speed flow, is then calculated from the pressure and internal energy, with the changes in it relaxed by a factor RF_PTRU, for which a typical value is 0.01. This density is then used to find the flow velocities from calculated values of the mass flux  ρV . 

The velocity of sound should initially be chosen to be about twice the maximum velocity expected in the whole flow field but it is automatically updated as the program runs to a set multiple of the maximum relative velocity in the whole flow field. The rate of updating is controlled by the input variable RF_VSOUND for which a typical value is 0.002, which means that the updates take around 500 time steps to settle down. This method can be used to speed up convergence for flows with Mach number less than about 0.25 or it can be used for extremely low Mach numbers less than 0.05, where the basic program may not converge. It can also be used for completely incompressible flows when the true density is simply input as data and is not re-calculated. The low Mach number option is called if ITIMST = 5  and the completely incompressible option is used if ITIMST = 6. If either option is used than the artificial speed of sound and relaxation factors on changes in speed of sound and in true density must be input as data. For completely incompressible flow then the fixed value of fluid density must also be input. 

## **REAL GAS PROPERTIES** 

**==> picture [506 x 76] intentionally omitted <==**

The advantage of this formulation is that the enthalpy and entropy can still be calculated analytically. 

The values of Cp1,  Cp2,  Cp3   and Tref  are input as data. For combustion products the values of Cp1, Cp2 and  Cp3    are approximately  1272.5,  0.2125   and  0.000015625  J/kg K    at  Tref  = 1400 K . The gas constant is held constant at  287.5 . 

This option is used if the value of Cp input in the standard data set is negative, in which case values of Cp1,  CP2,  Cp3 , Tref  and RGAS  are input in the next line of data. 

Steam properties are not available in MULTALL but an earlier version called MSTEAM contains a steam property routine. However, equilibrium steam can be reasonably well approximated as a perfect gas over the typical pressure range of a few stages. For low pressure wet steam values of Cp =  7300 J/kgK, gamma = 1.07 , are suggested. For dry steam at low pressures, typical values are Cp = 1970 J/kgK, gamma = 1.3. If steam changes from dry to wet within the region being calculated then it cannot be accurately modeled as a perfect gas. 

17 

## **LOOKUP TABLE FOR FLUID PROPERTIES** 

Version 20.9 includes to option to obtain the fluid properties from a “look-up-table” rather than from a perfect or semi-perfect gas model. The input properties for the table are density and internal energy since these are the variables calculated directly by the conservation equations. The table is “rectangular” in terms of these properties in that density is constant along one axis and internal energy along the other.  The table is searched using linear interpolation in each dimension. 

The properties which must be tabulated are:  Pressure, Temperature, Entropy, Isentropic Index for pressure-density (the equivalent of “gamma” for a perfect gas)  and Dryness Fraction. These may be generated from the COOLPROP routines, which are freely available. A short program for generating the required tables is provided, this must be linked to the COOLPROP software to be compiled and run. Tables for steam properties are provided. One table covers the likely range of low pressure steam turbines and one that of high pressure steam turbines, these tables use 70 x70 points to achieve acceptable accuracy without excessive run times. A larger, 150x150 point, table is also provided to cover the whole range of steam properties likely to be found in steam turbines. This table takes slightly longer to run but avoids the need to change the tables and recompile for different classes of turbine. 

A detailed description of this option is given in the file “lookup-table.doc” which is in this folder. 

## **BLADE REDESIGN OPTION** 

Using this feature it is possible to perform a limited redesign of the blade sections by generating new camber lines and thickness distributions. The stream surface coordinates are also changed. The method of specifying the new blade section is very similar to that in the author’s blade design system, STAGEN . 

A related option is to restagger the input blade, in which case blade is simply rotated about a specified axis so that its leading and trailing edge coordinates will change. The blade can also be leaned in the tangential direction, by a specified tangential distance relative to the hub section. 

## **REPEATING STAGE OPTION** 

In many multistage machines the flow repeats from stage to stage with the velocity profiles and stagnation pressure profiles remaining almost constant and only the stagnation pressure level changing. However, the shape of the stagnation temperature profile cannot remain constant since to do so would imply the same entropy rise for all streamlines. In reality the stagnation temperature will increase in the high loss regions near the end walls relative to that near mid span. When designing a single repeating stage it is desirable to try to satisfy this repeating stage condition and this can be done by automatically feeding back the exit stagnation pressure profile and yaw angle profile to the inlet boundary conditions. The stagnation temperature profile and pitch angle profile are not fed back but remain at the values input in the original data set. When run in this way the program naturally takes longer to converge but it saves multiple runs with manual adjustment of the boundary conditions. 

This option should only be used when a single stage is being calculated. 

18 

## **QUAS1 3D FLOW** 

Recent versions allow quasi-3D  (Q3D) flow on a blade to blade stream surface to be calculated with only a single cell being used in the spanwise direction. This is chosen by setting KM = 2, it enables Q3D solutions for a single blade row to be obtained in the order of 15 seconds. Viscous effects are included in the usual way on the blade surfaces but not on the stream surfaces. The stream surface is defined by the single surface on which the blade coordinates are input, together with a separate input of the relative stream surface thickness as a function of meridional distance. It is important to realise that the stream surface thickness has a very large influence on the blade loading and so it should be chosen realistically. The flow is forced to follow the stream surface by using a pressure difference between the two stream surfaces. This effectively produces a body force acting perpendicular to the surface so that it does not influence the flow on the stream surface. The value of this body force is controlled by the input value of Q3DFORCE but the value does not seem to be critical and values between 1.0 and 2.0 are usually acceptable, with higher values sometimes possible. 

Originally the quasi-3d option could only be used on a single blade row but in version 19.2 it has been extended to allow it to be used for multiple blade rows. If this is done then the results will depend greatly on the variation in stream tube thickness. 

To use this option set KM = 2 and input the value of Q3DFORCE in CARD 32. 

## **THROUGHFLOW MODE** 

The program can be run as an axisymmetric throughflow calculation. This is done if IM is set = 2 so there is only a single cell in the pitchwise direction. The blade geometry is input as usual, although an accurate blade profile is not essential, the exit blade centre line angle should be close to the required exit flow angle. Multiple stages can be calculated in this way. The number of grid points cam also be far less than for a 3D calculation and around 30 points streamwise and 15 points spanwise should be sufficient on each blade row. This gives fast run times of order 10 seconds per blade row. 

The flow is forced to closely follow a surface which is coincident with the centre line of the blade The blade loading is applied by calculating a blade surface pressure distribution which will force the flow to follow this centre line. This blade surface pressure distribution is not an accurate prediction of the actual distribution but is reasonably realistic. In particular the overall integrated (tangential force x radius) will balance the change in angular momentum of the flow. The surface pressures apply axial, radial and tangential forces to the flow and so the effects of three-dimensional blade geometry are included. The flow will depart slightly from the centre line because of smoothing of the blade loading, which is necessary to prevent discontinuities at the leading and trailing edges, this smoothing is useful in that it reduces the leading and trailing edge loading and so provides some deviation at the trailing edge. Extra deviation between the blade centre line and the exit flow direction can be input as data as is done in most throughflow calculations. 

The loss may be calculated by the same loss routines as used for 3D flow but these will not be accurate with only 2 grid lines. It is suggested that the option using YPLUSWALL is used, this will 

19 

apply a constant skin friction factor on the blade surfaces equal to  2/(YPLUSWALL)[2] and so a value of YPLUSWALL = 20 will give a realistic skin friction coefficient of 0.005 . The optimum value of YPLUSWALL can be chosen to agree with experience.  Tip leakage can be included in the usual way but it is only driven by the difference between the inlet flow direction and the blade surface, not by a pressure difference between the pressure and suction surfaces, and so the leakage will be less than in reality. 

In the throughflow mode the flow along each streamline is effectively one dimensional with a flow area equal to the local passage width measured perpendicular to the flow. This means that, with supersonic flow, the flow will behave as in a one-dimensional nozzle. It will choke at a point of minimum area and the downstream expansion will be terminated by a normal shockwave. The method cannot predict the oblique shock waves that are common in turbomachines and the calculated blade loading in such cases will not be realistic. This is common to all time-marching throughflow methods unless they specify the local tangential velocity rather than the flow direction.  In the later case only shock waves with an upstream axial Mach number greater than one can be predicted.  However, the present method does predict the supersonic deviation found on turbine blades with supersonic exit flow. 

## **COMPILING THE PROGRAM** 

The program is written in very standard FORTRAN77 and should compile and run on any computer with a FORTRAN compiler. The only non-standard routine is the timing call, which evaluates the CPU time per time step. This will vary for different compilers and operating systems. At present the “MCLOCK” routines for the LINUX  g77 and  gfortran  compilers are coded but these may need changing. The timing calls are not essential for the running of the program and can be removed or commented out if not required, or if the program will not compile with them present. 

All the variables are declared and dimensioned within a single common block, e.g. “ **commall_open** ” which must be present in the same directory as the program when is compiled. The sizes of the arrays are declared by PARAMETER statements in  “ **commall_open** ”. Typical maximum dimensions of the grid would be 65 points in the pitchwise and spanwise directions and 1000 points in the streamwise (J) direction. With these dimensions the program uses about 750 MBytes of memory.  The large number of streamwise grid points is only needed for multistage calculations with many blade rows, typically about 120 points per blade row would be sufficient. There is no limitation on the size of the arrays apart from those due to computer memory limits. If the program will not compile due to insufficient computer memory then, under LINUX, the available memory may be extended by adding  “ -mcmodel=medium “ to the end of the compilation line.   e.g.     gfortran –O  –o test.x  test.f –mcmodel=medium  .  Similar extensions are probably available for other compilers and can be searched for on the internet. 

The speed of execution is generally increased by using the highest level of compiler optimization available.  For a throughflow calculation, with IM = 2 , the speed is increased if the dimension ID is set = 2 in the parameter statement of “ **commall-open”** . 

20 

## **RUNNING THE PROGRAM AND INPUT AND OUTPUT FILES** 

Before trying to start the program the file  “ **intype** ” must be created in the same directory. This contains the single character “O”  or “N”  deciding whether the “ **old** ”  or   “ **new** ”  input format will be used. 

The main input data is read from FORTRAN unit 5. The file name is not specified within the program and so the program is most easily run using a command such as 

MULTALL .X <  DATA.IN 

Where MULTALL.X is the name of the compiled executable code and DATA.IN is the name of the data file. The program will run either until the average residual reaches the specified tolerance, CONLIM, or for the maximum number of time steps specified, NMAX. 

Several different output files are produced. The standard output is to FORTRAN unit 6, which defaults to the screen, this gives a summary of the convergence history every 5 time steps and a more detailed average of the flow properties every 200 time steps. If it is required to send this output to a file then use a command such as 

MULTALL.X  <  DATA.IN  > RESULTS.OUT 

Where  RESULTS.OUT is the name of the output file. 

Other output files are set within the program and are produced automatically. These are: 

“ **stage.log** “  A formatted file containing the convergence history with values of the rms error, continuity error and inlet mass flow is written to FORTRAN unit 4 output every 5 time steps. This file may be used to plot out the convergence history using program **histage** . 

“ **flow_out** ”   An  unformatted file containing the all the flow properties is written to FORTRAN unit 7. This file may be output after specified numbers of time steps. It is also automatically output on convergence or on reaching the specified maximum number of time steps. This file, together with the file  “ **grid_out** ”  may be used to plot out the results.  The same file is also used as a restart file if a restart is requested. 

“ **grid_out** ” An unformatted file containing the grid coordinates is written to FORTRAN unit 21. It is used, together with “ **flow_out** ”, to plot out the results. 

‘ **global.plt** ” An unformatted file containing the one-dimensional mass averaged flow data is written to FORTRAN unit 11. This may be used by program **globplot** to plot out the one-dimensional variation of mass flow, stagnation pressure, stagnation temperature entropy or lost efficiency along the flow path. 

“ **results.out** ” A formatted file containing selected flow properties is written to FORTRAN unit 3. The properties may be selected as described in Note 7. This file may be very large and so the output 

21 

requested should be chosen carefully. Usually no output should be requested except for possible debugging. 

“ **loss-co.plt** ”  A formatted file which contains the loss of isentropic efficiency at every “J’ station is written to FORTRAN unit 23 at the end of any run and may be used to plot lost efficiency against meridional distance. 

“ **mixbconds** ” A formatted file written to FORTRAN unit 12.  This contains the mixed out values of the flow properties at each mixing plane at every spanwise (K)  grid point. It may be used to provide the inlet boundary conditions to a subsequent calculation on an individual blade row or smaller group of blade rows. 

The plotting programs that use some of these files are based on the HGRAPH plotting package and so are not publicly available. 

There is an option to stop the program and write out the results and a plot file at any time. Every 10 time steps the program opens and reads a file named “ **stopit** ” which may be opened and edited by the user whilst the program is running. This file contains a single number, if the number is zero the execution will continue, if it is  1   then the execution ends and the results files are written. To stop execution, pause the program,  edit “ **stopit** ” and type  1  in place of the  0 ,  then restart execution of the program . 

J D DENTON Updated for MULTALL_OPEN-20.9   November 2020 



# --- END OF SOURCE: General-description.pdf ---



# ========================================================
# START OF SOURCE: Inverse-design mode .pdf (Category: Multall Documentation)
# ========================================================

## **THE QUASI-3D INVERSE DESIGN MODE** 

## **INTRODUCTION** 

MULTALL-OPEN-20.6 has been developed to work in the inverse mode in which a blade surface pressure distribution is input and a blade producing that distribution is designed. At present this is limited to quasi-3D (Q3D) calculations on a blade-toblade stream surface but it is hoped to extend it to a fully 3D design mode in future. The calculation remains fully viscous and the stream surface thickness and radius can change through the blade row. Both suction and pressure surfaces of the blade can be specified but this does not allow any control on the blade thickness, which may become negative. To overcome this an option to relax the thickness to a specified value is included, when this is used the pressure surface pressure distribution will differ slightly from that specified but the suction surface pressures should still be correct. 

The method works especially well at high Mach numbers and is particularly good a cancelling shock wave interactions with the blade surfaces. However, it is difficult to avoid generating shocks at the leading or trailing edges of high Mach number blades. Run times are of order 2 minutes for an initial design but several iterations may be needed. 

## **METHOD** 

Several algorithms for moving the blade surfaces have been tried but the only one which seems generally useable is when the condition of no flow through the blade surface is replaced by a condition in which the local flow through the blade surfaces is proportional to the difference between the specified pressure the currently calculated pressure.  The mass flux through the blade surfaces is updated in this way on every time step. If flow is entering the blade from the main stream then its properties are taken as those on the blade surface, if flow is entering the mainstream through the blade surface then its properties are taken to be those at one grid point away from the surface. This simple expedient is stable and has negligible effect on the accuracy since the surface flows should become zero on convergence. After doing this for about 500 time steps new surface streamlines are calculated and the blade geometry is updated to follow them. This process is repeated until the changes in geometry become negligible, usually after a maximum of 40 updates, in most cases the geometry will become fixed after far fewer updates. 

The calculation is best started from a standard MULTALL data set for an initial approximate design of the blade, which can be obtained from STAGEN. This initial design sets the blade pitch:chord ratio (i.e. number of blades) and the inlet and exit boundary conditions. This data set is run to near convergence, typically 2500 steps, before the inverse mode is started. After that the calculation is continued and on every time step the surface mass flows are calculated as described above. The surface mass flows are summed to find the net flow through the surface and on the suction surface the average flow is then subtracted from the local flows so that the net flow becomes zero. On the pressure surface the surface mass flows are summed as above but when the average flow is subtracted from the local flows it is adjusted so as to provide a 

specified trailing edge thickness. This is continued on every time step for typically 500 steps, without changing the blade geometry. 

Around every 500 time steps the blade geometry is updated. Starting from the leading edge point, which remains fixed, the surface flows are summed to trace a new surface streamline. If the net surface mass flux is zero then the trailing edge point will also remain fixed but if a trailing edge thickness is specified the net flux on the pressure surface will be adjusted to provide that thickness. The blade geometry is then relaxed towards the new calculated surface streamlines, the relaxation factors are input as data but are typically 2.0. However, fixing the leading and trailing edge points is too great a constraint on the blade geometry and so the required exit flow angle must also be specified and at every geometry update the blade is rotated (strictly sheared) to try to achieve that angle. 

Since the blade loading (i.e. angular momentum change), the pitch:chord ratio  and the exit Mach number have been specified there is only one compatible exit flow angle. If the specified flow angle does not agree with this then the specified blade loading cannot be achieved. Nevertheless the calculation should converge and will usually obtain blade surface pressure distributions which are very similar in shape to those specified but which differ in pressure level, so as to match the imposed exit angle. The blade obtained will usually be a good design for the specified exit flow angle. However, the compatible exit flow angle and the compatible pitch:chord ratio (number of blades) are calculated (this is surprisingly difficult) and are printed out at the end of the calculation. For a specified blade spacing (pitch/chord ratio) and a specified exit Mach number there is a maximum possible angular momentum change of the flow, which usually occurs when the exit angle is about +/-45deg. If the specified load exceeds this maximum load then the iteration to calculate the compatible exit angle will not converge and the value printed out will probably be close to zero or to 90deg. The iteration may also be unstable when the exit angle is close to +/-45 deg as there are then two possible angles for the same loading, one greater than 45deg and one less. If the iteration does converge, and the compatible exit flow angle printed out is realistic, then the calculation may be repeated with either the number of blades changed to the compatible number, in which case it should produce a design with the specified surface pressures and the specified exit angle, or with the specified exit angle changed to the compatible angle, in which case it should produce a design with the specified blade numbers and the specified surface pressures. An alternative option is to iteratively adjust the specified exit flow angle to the calculated compatible angle during the calculation. This works satisfactorily for low exit angles, say <  65deg or > -65deg,  but may become unstable for higher angles and it clearly will not work if the iteration to find the compatible angle does not converge, and so should be used with caution. 

Specifying both blade surfaces in this way allows no control on the blade thickness which may become unacceptably thin or even negative. To try to avoid this a minimum acceptable thickness, equal to some fraction of the initial blade thickness may be specified. Also a specified thickness can be set, this is a multiple of the initial blade thickness plus specified leading and trailing edge additions. On every geometry update the new blade thickness can be relaxed towards this specified thickness. If the input relaxation factor is zero then the thickness obtained is that calculated from the specified pressure distribution alone, if the relaxation factor is 1.0 the thickness will 

be close to the specified thickness. In the latter case the surface pressure distribution will differ from that specified and continuity will not be satisfied because the flow through the blade surfaces will not become zero. In many cases a low relaxation factor, say 0.1, can be used and the pressure distribution obtained will then be very similar to that specified and the thickness will be realistic. Specifying the blade thickness only affects the flow on the pressure surface and the suction surface geometry is always obtained from the specified pressure distribution. 

The calculation is first run for NINV_START time steps without any geometry change to build up a near converged solution for the initial design. The blade geometry is then updated every NINV_UP steps until a total of NINV_END steps have been performed. About 40 geometry updates are usually sufficient to obtain the final blade shape, although in many cases far less than this are needed, so if NINV_START is 2500 and NINV_UP is 500 then NINV_END would be about 22,500, 25,000 is often used. It is usually desirable to continue the calculation a little further, without changing the geometry, to ensure that the final solution if fully converged on the new geometry, so NSTEPS, as set in the main MULTALL data set, should be about 2000 steps greater than NINV_END. 

## **RUNNING THE INVERSE MODE** 

The program starts by reading in a standard MULTALL data set, the only addition to that is to input a new variable, IF_INV, along with the existing IF_RESTART in card 9.  If IF_INV is not present or is zero than a conventional MULTALL calculation is performed. If IF_INV = 1 then the inverse design mode will be used. One other change to a standard MULTALL data set may be needed, it has been found that the datum stream surface thickness, which was fixed at 5% of the blade chord, may be too thick when stream surfaces are curved causing the blade geometry to vary between the two surfaces.  To prevent this an option to read in the datum stream surface thickness is added to Card  Q3D1 which now reads in Q3DFORCE  and TKSS_REF, the latter should be set to a lower value, typically 0.02 , although the original datum of 0.05 is OK in most cases. Too low a value of TKSS_REF may cause instability. 

If the inverse mode is specified then data is also read in from a new input file called “inverse.in” the details of which are described below.  This contains the values of NINV_START,  NINV_END and NINV_UPP , the specified blade surface pressure distribution and various control parameters as described in the next section. 

Although the calculation may be started with an arbitrary guess of the required surface pressure distributions this is unlikely to produce a blade loading compatible with the required exit flow angle and boundary conditions. Hence it is best to start from the pressure distribution of an initial design and iteratively improve it. The initial blade geometry, which may be generated by STAGEN, should be as close as possible to the required final design. In particular the initial geometry sets the number of blades (pitch:chord ratio), the inlet and exit flow conditions and the stream tube thickness and radius. Its surface pressure distribution should be as close as possible to that required for the final design, in fact the method works best when it is used to make minor changes to an existing blade. 

To do this set IF_INV =1 and NSTEPS = 5010 in the main MULTALL data set. Also set the convergence limit, CONLIM, to a very small number, say 0.000001, to prevent premature convergence. Set NINV_START = 5000 in the ”inverse.in” data set.  The specified pressures in “inverse.in” will not be used at this stage and so can be arbitrary. 

Run the calculation and after 5000 (NINV_START) steps it will write the current solution to a new file called  “initial_inverse.in”, this contains a smoothed copy of the blade surface pressures calculated for the initial design. The calculation will stop after NSTEPS (5010) steps. No inverse calculations have been performed at this stage. 

Copy “initial_inverse.in”  to  “inverse.in”.  Inspect the surface pressure distributions and adjust them to change any undesirable features whilst trying to maintain the average pressure roughly constant on each blade surface. Change NINV_START to 2500 and NINV_END to 25000 in “inverse.in”.  Now reset NSTEPS to NINV_END + 2000 in the main data set, start the calculation with this new version of “inverse.in” and run to completion after NSTEPS  steps. 

Inspect the calculated blade pressure distributions and decide if further changes are necessary, if so copy the output file  “final_inverse.in” to “inverse.in”, change the specified pressures and run again. Note that the pressure distributions in “finalinverse.in” should be compatible with the specified exit flow angle and so may be different from those in “initial_inverse.in” which are not necessarily compatible with the specified exit angle. 

If the blade thickness is not acceptable then either the specified pressure distributions can be changed or the blade geometry may be relaxed towards a specified thickness distribution. In some cases the blade thickness obtained is extremely sensitive to the specified pressures around the leading edge and these should be adjusted very gradually, similarly the trailing edge thickness can be extremely sensitive to the local pressures. 

It is found that increasing the specified pressures near the leading edge and reducing them near the trailing edge generally thickens the blade, and vice-versa to thin it. This may be thought of as adding sources near the leading edge and sinks near the trailing edge. To help with this an option to add linear variations of specified pressure is included. Pressures PADD_I1 and PADD_IM  are input in ‘inverse.in” and a linear variation of pressure with meridional distance from +PADD_I1 at the leading edge to –PADD_I1 at the trailing edge is added to the specified pressures on the I=1 blade surface, similarly for PADD_IM. This linear variation in pressure does not affect the total blade loading.  To thicken the blade usually set PADD_I1 = PADD_IM with both of them positive, typical values depend on the Mach number levels but for near sonic conditions PADD_I1 = PADD_IM = 3000 N/m[2] is typical. Making PADD_I1 and PADD_IM the same changes the loading distribution but not the overall load on the blade. 

The specified thickness distribution is obtained by first scaling the initial thickness by FTK_SCALE then adding an additional thickness (TK_ADD_LE x meridional chord) near the leading edge and (TK_ADD_TE x meridional chord) at the trailing edge. Both TK_ADD_LE and TK_ADD_TE can be negative if it is required to locally thin 

the blade.  On every geometry update the thickness is relaxed towards this specified thickness by a factor RF_THICK, this is in addition to the thickness changes made from the main algorithm.  A low value, say RF_THICK = 0.1, will often provide a realistic thickness without seriously compromising the pressure distribution. A high value, RF_THICK = 1.0, will give close to the specified thickness distribution but the pressure distribution on the pressure surface will be significantly compromised and continuity will not be satisfied. It is sometimes found that increasing the leading edge thickness also increases the trailing edge thickness and it is hard to overcome this. 

The trailing edge thickness is set by the scaled initial thickness plus TK_ADD_TE even when RF_THICK is zero. This is achieved by adjusting the pressure surface mass flux and does not cause a continuity error. 

There is no clear convergence criterion, the changes in flow on each geometry update should reduce gradually but will seldom become zero. Generally convergence may be assumed when EAVG becomes less than 0.0005 and ECONT is less than 0.01. If the EAVG values do not reduce after many geometry updates then the relaxation factors RFAK_I1 and RFAK_IM  should be reduced and the rotation factor, ROT_FAK, may also need to be reduced.  ECONT may not become low (< 0.01) if the blade thickness is being forced via RF_THICK. 

On completion the program writes out the conventional MULTALL output files plus a file named “newgrid” , this contains the new blade upper (I=1) surface coordinates and new blade thickness. They may be cut and pasted into the original MULTALL data set to obtain a data set for the redesigned blade. The blade axial and radial coordinates are not changed from those in the initial data set. 

A warning on plotting the resulting geometry, if using the original plotting program PLOTALL-17.1.  In previous versions of MULTALL the blade geometry is only passed to the plotting file once at the start of the calculation (because in a conventional calculation it does not change) and previous versions of the plotting program PLOTALL only read the geometry file once. The latest version MULTALLOPEN-20.6 writes the geometry file every time that an output is requested, using NOUT.  If the old plotting program PLOTALL-17.1 is used for output from the inverse mode then only the geometry of the first plotter file to be output will be used and plotted, this will be different from any later outputs of the modified design. Hence the option to use NOUT to output multiple plot files during the iterations should not be used. Only the final solution should be plotted. A modified version of the plotting program, PLOTALL-20.1, is attached and should be used with output from version 20.6, this will read in and plot the correct geometry for each output requested so NOUT can be used. 

## **DATA INPUT FOR THE FILE “inverse.in”** 

## **All data is in Free Format.** 

CARD 1 IFINV_I1,  IFINV_IM IFINV_I1 Design the I = 1 surface if this = 1, do not design it if it = 0. IFINV_IM Design the I = IM surface if this = 1, do not design it if it = 0. 

## **IF IFINV_I1 = 1 then input the following data, Cards 2 and 3** 

CARD 2 NIN The number of points at which the I = 1 surface pressure will be input, typically about 20 points. CARD 3 For  N = 1 to NIN read     X_IN(N), P_IN(N) X_IN(N) The fraction of meridional chord at which the pressure is being input. P_IN(N) The specified blade surface pressure on the I = 1 surface at these points. In N/m2 . 

## **IF IFINV_IM = 1 then input the following data, Cards 4 and 5** 

CARD 4 NIN The number of points at which I = IM surface pressure will be input, typically about 20 points. CARD 5 For  N = 1 to NIN read      X_IN(N), P_IN(N) X_IN(N) The fraction of meridional chord at which the pressure is being input. P_IN(N) The specified blade surface pressure on the I = IM surface at these points. In N/m2 . 

CARD 6 A2_SPEC_DEG The specified exit flow angle in degrees. This is positive if the associated flow vector has a positive component in the direction of rotation. 

|CARD|7|ROT_FAK|<br>A relaxation factor on the change in exit flow|
|---|---|---|---|
||||angle between iterations. Usually it is OK to set|
||||this =1.0 but reduce it to 0.5 if any instability in|
||||the exit angle or mass flow rate.|
|CARD|8|ANG_FAK|<br>The specified exit angle is relaxed towards a|
||||calculated compatible angle by this factor on|
||||every iteration. If this  option is to be used set|
||||ANG_FAK = 0.1, set it = 0.0 to keep the|
||||original specified angle A2_SPEC_DEG. The|
||||process is sometimes unstable especially at high|
||||absolute values of angle, say greater than 65 deg|
||||so use it with caution.|
|CARD|9|RFAK_I1, RFAK_IM||
||||Relaxation factors on the changes in blade|
||||geometry on the  I =1 and I=IM blade surfaces.|
||||Usually set both = 2.0 but reduce to 1.0 or even|
||||0.5 if the geometry changes are not converging.|
|CARD|10|N_SMTH,|F_SMTH|
||||The blade surface movements are smoothed by|
||||N_SMTH passes of a smoothing with smoothing|
||||factor F_SMTH. This helps stability. Typically|
||||set N_SMTH = 5, F_SMTH = 0.5. Increasing|
||||N_SMTH improves stability without|
||||significantly compromising the final solution.|
|CARD|11|NINV_START,  NINV_END,  NINV_UPP||
||||The inverse mode starts after NINV_START|
||||steps, typically 2500.|
||||The geometry changes end at NINV_END|
||||steps, typically 25000 .|
||||The blade geometry is updated every|
||||NINV_UPP steps, typically 500 but it may be|
||||desirable to increase it for cases with a large|
||||number of grid points which are slow to|
||||converge.|



|CARD|12|FTK_SCALE,|FTK_MIN, TK_ADD_LE, TK_ADD_TE,|
|---|---|---|---|
|||RF_THICK,  JSET_TK||
|||FTK_SCALE|The initial blade thickness is scaled by|
||||FTK_SCALE before being used to set|
||||the specified thickness.|
|||FTK_MIN|The original thickness is scaled by|
||||FTK_MIN to set the minimum|
||||acceptable thickness.|
|||TK_ADD_LE|An addition thickness TK_ADD_LE  x|
||||(meridional chord) is added at a grid|
||||point JSET_TK points behind the|
||||leading edge. This is added to the scaled|
||||thickness of the original blade to obtain|
||||the specified thickness.|
|||TK_ADD_TE|An additional thickness TK_ADD_TE x|
||||(meridional chord) is added at the|
||||trailing edge. This is added to the scaled|
||||thickness of the original blade to obtain|
||||the specified thickness.|
|||RF_THICK|The thickness is relaxed towards the|
||||specified thickness by RF_THICK. Set|
||||= 0 to use the thickness obtained from|
||||the specified pressure distribution on the|
||||pressure surface. Set = 1.0 to use the|
||||specified thickness. Typically set 0.1 to|
||||obtain a suitable compromise.|
|||JSET_TK|The leading edge thickness,|
||||TK_ADD_LE,  is applied at JSET_TK|
||||grid points downstream of the leading|
||||edge.  Upstream of this point an elliptic|
||||thickness distribution is applied.|
||||Typically JSET_TK = 5 .|



**Note** All the thickness referred to above are the tangential thickness. 

CARD 13 PADD_I1, PADD_IM PADD_I1 The specified pressure on the I=1 blade surface is increased by PADD_I1 at the leading edge and decreased by PADD_I1 at the trailing edge with a linear variation with meridional chord between those points. In  N/m[2 ] . PADD_IM The specified pressure on the I=IM blade surface is increased by PADD_IM at the leading edge and decreased by PADD_IM at the trailing edge with a linear variation with meridional chord between those points. In N/m[2] . **Note** Making both PADD_I1 and PADD_IM positive tends to thicken the blade and making them both negative tends to thin it. Typical values depend on the Mach number level but for near sonic conditions values of a few thousand N/m[2] are typical. 

## **TEST CASES SUPPLIED.** 

The initial design MULTALL file and the final “inverse.in”  file are supplied for the following test cases. 

|aerofoil.dat|A simple aerofoil with a shock which is cancelled before it hits|
|---|---|
||the suction surface.|
|impulse-turbine .dat|An impulse turbine rotor with the suction surface just above|
||Mach 1 but no shocks.|
|hp-turb-stator.dat|A typical high pressure gas turbine stator with exit Mach|
||number about 1.0 and continuous acceleration on the blade|
||surfaces.|
|lp-aero-turbine.dat|A typical low pressure aero engine blade, very thin, with Mach|
||number just subsonic.|
|compr-hub.dat|A typical compressor hub section, high subsonic.|
|supercrit.dat|A compressor rotor with peak Mach number around 1.2 but no|
||shocks on the suction surface.|
|trans-fan.dat|A transonic compressor blade with inlet Mach number around|
||1.3 but with the bow shock cancelled before it meets the|
||suction surface.|



|low-reacn.dat|A low reaction turbine rotor blade.|
|---|---|
|highmach-nozzle.dat|A typical last stage LP steam turbine stator with exit Mach|
||number 1.8.|
|lp-st-tip-20k.dat|A last stage LP steam turbine rotor tip section with exit Mach|
||number around 1.8.|
|lp-st-mid.dat|A last stage LP steam turbine rotor mid section with radius|
||change and stream tube divergence , exit Mach number around|
||1.5|
|lp-st-hub.dat|A last stage LP steam turbine hub section, near impulse with|
||stream tube divergence and shock cancellation.|
|rad-casc+rotn.dat|A rotating radial flow cascade with geometry typical of a|
||centrifugal compressor.|
|mixed-fan.dat|A mixed flow, low speed, fan impeller with radius change and|
||stream tube contraction.|
|ogv.dat|An outlet guide vane from a LP aero engine turbine.|





# --- END OF SOURCE: Inverse-design mode .pdf ---



# ========================================================
# START OF SOURCE: lookup-table.pdf (Category: Multall Documentation)
# ========================================================

## **USING A LOOK UP TABLE FOR FLUID PROPERTIES** 

Version 20.9 includes the option to obtain the fluid properties from a lookup table rather than from a perfect or semi-perfect gas model. 

The properties are tabulated as functions of density and specific internal energy since these are the primary fluid properties calculated by the solver. The table is “rectangular” in the sense that the density varies along one axis, the “I” axis and the internal energy along the other, “J” axis, i.e.  for a given value of “I” the density is the same for all “J” values and for a given value of “J” the internal energy is constant for all “I” values. The values need not be uniformly spaced and for the density in particular a geometric progression in spacing is better because it varies over such a wide range, e.g  0.02  to 200 kg/m[3] ,  for steam.  The internal energy varies over a much smaller range and its values may be evenly spaced. 

The properties which must be tabulated are : 

Pressure. Temperature. Entropy. Isentropic Index Dryness Fraction. 

The pressure:density relationship for a small isentropic expansion.  i.e. gamma in P/rho**gamma = constant. 

The entropy and dryness fraction are not used at all during the calculation but are output to the plotting file so they can be visualised in the solution. 

The tables must be named “props_table.dat” and must be in the same directory from which the solver is being run. 

The table is searched using a bilinear interpolation in which it is first divided into coarse, typically 8x8, blocks, these are searched to find the coarse block containing the input values and this is then searched cell by cell to find the matching point. The size of the table depends on the range of properties to be covered, for typical high pressure or low pressure steam turbines 70x70 blocks are sufficient but the whole range of properties likely to occur in steam turbines may be covered by a 150x150 point table. The latter takes slightly longer to run than the smaller tables but, unless run time is at a premium, it is simpler to use the same table for all runs. Suitable tables for high pressure steam turbines, low pressure steam turbines and the whole range of steam conditions likely in steam turbines are provided. These must be copied to  “props_table.dat”  before being used. 

The format required for the tabulated data is described below. The required tables can be generated from the COOLPROP system of fluid properties (www.coolprop.org ) using the Fortran program  “ make-all-tables.f  “ which is included in this folder.  This must be linked to the COOLPROP system and compiled before it can be run. The COOLPROP system is not easy to use and the author cannot give any guidance on it. The program “make-all-tables.f “ is set up for steam and to cover the whole range of likely steam turbine properties with a 150x150 table. It can easily be changed to use other gases, different property ranges and different table sizes if required. 

COOLPROP sometimes gives overflows near discontinuities in the fluid properties, e.g. near the saturation line for steam. To prevent this causing failure the tabulated values are searched by MULTALL, before they are used, any large changes between adjacent points are smoothed over. 

## **DATA INPUT TO USE A LOOKUP TABLE** 

There is very little change to the input data compared to recent versions of MULTALL. The changes are described in  “new-readin-input-data-20.9.doc” . 

In CARD 2 now read in   CP, GAMMA, IFGAS  instead of just CP and GAMMA. Set IFGAS =0 for a perfect gas, 

Set IFGAS = 1 for a semi-perfect gas with Cp a function of temperature. Set IFGAS = 3  to use a lookup table. 

If IFGAS is not included then it defaults to zero. 

In CARD 77 Read in HOIN(K) instead of TO1(K) . 

HOIN(K) is the inlet stagnation enthalpy in  kJ/kg . 

Also the file “props_table.dat “ must be available in the directory from which the program is being run. 

## **PLOTTING THE OUTPUT WHEN USING A LOOKUP TABLE** 

The plotting routine “plotall” uses the gas constant and specific heat ratio to evaluate flow quantities, hence some quantities are not accurate when the fluid properties are obtained from a lookup table. The velocities and density and mass fluxes are accurate but pressure, temperature, Mach number and entropy are not. If the usual plotting program, “plotall-20.1”, is used with a lookup table solution the output from MULTALL has been slightly changed so that item 9 on the menu is the true static pressure and item 33 is the true entropy.  A modified version of the plotting program, “ plot-steam.f” has been developed to give accurate plotted quantities when using a lookup table. If a lookup table is used the solver outputs extra data to the plotting file “flow_out”, this is read in and used by “plotall-steam”,  hence “plotall-steam” cannot be used for solutions which do not use a lookup table. A version of “plotall-steam” compiled for LINUX is provided. 

## **INPUT DATA FOR THE PROPERTY TABLE** 

Note that all the data in this file is read in to MULTALL as “Free Format”. However, the tables can be much more easily understood and checked for any errors if they are written out as formatted data. This is done by program  “ make-all-tables.f “ . 

In order to be read by MULTALL this file must be named  “props_table.dat” .  Any queries about the data input can usually be answered by studying the tables provided for steam, e.g. “HP-steam-tables.dat”. 

CARD 0. COMMENT CARD 

CARD 1. ITAB, JTAB ITAB The number of input data points in then “I” dimension JTAB The number of input data points in then “J” dimension CARD 2. COMMENT CARD CARD 3. ROAXIS(I) , I =1,ITAB ROAXIS The values of density along the “I” axis of the tables. They need not be uniformly spaced and are usually best spaced as a geometric progression.  In kg/m[3] . CARD 4. COMMENT CARD CARD 5. UAXIS(J) , J =1,JTAB UAXIS The values of internal energy along the “J” axis of the tables. They need not be uniformly spaced but  it is usually acceptable if they are.  In J/kg . CARD 6. COMMENT CARD CARD 7. COMMENT CARD CARDS 8. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   RO_TAB(I,J),  J=1,JTAB RO_TAB The tabulated values of density. In kg/m[3 ] . These do not vary in the J direction and the value in the I direction must  be the same as ROAXIS in CARD 3 . CARD 9. COMMENT CARD CARD 10. COMMENT CARD CARDS 11. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   U_TAB(I,J),  J=1,JTAB U_TAB The tabulated values of internal energy. In J/kg .These do not vary in the I direction and the value in the J direction must  be the same as UAXIS in CARD 5 . 

CARD 12. COMMENT CARD CARD 13. COMMENT CARD CARDS 14. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   P_TAB(I,J),  J=1,JTAB P_TAB The tabulated values of static pressure. In N/m[2] . CARD 15. COMMENT CARD CARD 16. COMMENT CARD CARDS 17. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   T_TAB(I,J),  J=1,JTAB T_TAB The tabulated values of static temperature. In K . CARD 18. COMMENT CARD CARD 19. COMMENT CARD CARDS 20. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   ENT_TAB(I,J),  J=1,JTAB ENT_TAB The tabulated values of entropy. In  J/kg K . This is not used in the calculation but is useful for the output. CARD 21. COMMENT CARD CARD 22 COMMENT CARD CARDS 23. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   GA_PV_TAB(I,J),  J=1,JTAB GA_PV_TAB The tabulated values of isentropic index for a small pressure-density change i.e.  gamma  in P /rho**gamma = constant along an isentropic. 

CARD 24. COMMENT CARD CARD 25. COMMENT CARD CARDS 26. FOR I = 1 to ITAB READ COMMENT CARD READ COMMENT CARD READ   DRY_TAB(I,J),  J=1,JTAB 

DRY_TAB The tabulated values of fluid dryness fraction. This is not used in the calculation but is useful for the output. 



# --- END OF SOURCE: lookup-table.pdf ---



# ========================================================
# START OF SOURCE: Meangen-differences.pdf (Category: Multall Documentation)
# ========================================================

## **Differences between MEANGEN-17.1  and MEANGEN-17.2** 

The main difference is that the “STAGEN.DAT” file written by MEANGEN-17.2 has the values of gas constant, RGAS,  and specific heat ratio, GAMMA,  as the first line of data.  This can then be read by STAGEN-17.2. 

The file written by MEANGEN-17.1 does not include RGAS  and GAMMA as these are set by default in STAGEN-17.1 . The file can be read by STAGEN-17.1 but the program should be edited to change the defaults values of RGAS and GAMMA if necessary. 

Other changes does not affect the input or output but include making an estimate of the mean height density, as opposed to the mean stream surface density, for working out the volume flow. This should give a better estimate of the annulus area. 

## **MEANGEN-17.4 added on 3/10/2017** . 

A new version  MEANGEN-17.4   has been  added. This has additions to include a blockage factor, which is sometimes used in compressors to allow for the blockage due to the growth of the annulus boundary layers. It also allows the amount of blade twist to be scaled from the free vortex value so that untwisted or over-twisted blades can be generated. In addition the blade sections can be individually rotated by an amount specified in the input data, the actual rotation is performed in STAGEN. 

Because of these additions previous MEANGEN.IN data sets are not quite compatible with version 14.4 although they can easily be updated. Three new data sets for the new version have been added to the sample data sets provided. 



# --- END OF SOURCE: Meangen-differences.pdf ---



# ========================================================
# START OF SOURCE: meangen-instructions.pdf (Category: Multall Documentation)
# ========================================================

## **MEANGEN  DESCRIPTION** 

MEANGEN  is a mean-line turbomachinery design program which produces a data set for use with STAGEN and MULTALL. It works with compressors and turbines and for axial or radial flow machines. Given the basic design parameters such as mass flow rate, rotational speed, mean radius, etc, it evaluates the flow angles and blade heights and makes an initial guess of blade shapes. It is designed to work with the minimum of user input and so many of the parameters needed are set by default. The use of the defaults is described by comments in the code, they can be changed by editing and recompiling the program. 

An update for MEANGEN 17.4  is included at the end of this document. 

MEANGEN will produce a basic initial design with no allowance for more complex features such as tip leakages, cooling flows, bleed flows, etc. These features must be added later by editing the output file “ **stagen.dat** ” , or in some cases by editing the input file to MULTALL. 

The program is written in standard FORTRAN77 and should run on any machine with a FORTRAN compiler. It was developed using the LINUX  “ **gfortran** ” compiler. 

To run the program, first compile it ,  then type the name chosen for the executable code , e.g. **meangen.x** ,  and then answer the questions that appear on the screen. If you choose to input the data from a file it must be named  “ **meangen.in”** . 

The data input to the program can be produced either by answering questions on the screen or from a file named “ **meangen.in** ”. When first run on a new design the input will usually be from the screen, but the program writes an output file called “ **meangen.out** ” which mirrors the screen input and on future runs, with only small changes to the same basic design, the input is most easily changed by copying this file to “ **meangen.in** ”  and then editing “ **meangen.in** ” .  An example of “ **meangen.in** ” is shown at the end of this note. The detailed data input requirements are described by comments in the FORTRAN,  which can be seen by studying the code, or by the annotated output file “ **meangen .out”** . 

MEANGEN writes an output file called “ **stagen.dat** ” which will immediately run on the 3D geometry generating program STAGEN, which in turn writes an input file for the 3D solver MULTALL. Using the combination a 3D solution can usually be started in minutes and a 3D solution obtained in of order ½ hour. 

Meangen basically designs complete stages or multiple stages rather than single blade rows although the latter can be generated, as described later. One of the first questions asked on the screen is whether the machine is a turbine or a compressor. **For a turbine the first blade row must be the stator and for a compressor the first row must be the rotor. The direction of rotation is always in the positive circumferential (theta) direction.** 

The angle convention is illustrated below. All angles are positive if the associated velocity vector has a positive component in the direction of rotation. Hence compressor rotor inlet angles and turbine rotor exit angles will always be negative and compressor stator inlet angles and turbine stator exit angles will always be positive. 

**==> picture [303 x 175] intentionally omitted <==**

There are a variety of options for specifying the stage geometry. 

The simplest option is if it is chosen to design an axial flow machine with repeating stages. This means that each stage has a fixed mean radius and constant axial velocity and with the velocity magnitude and direction being the same at stage inlet and exit.  This option is chosen by setting FLO_TYP = “AXI” when requested on the screen. The velocity triangle is then the same at stage inlet and outlet and it is only necessary to specify 3 geometrical or flow parameters to fix the velocity triangles.  These can be any 3 chosen from: 

Stator inlet flow angle, α1 Stator exit flow angle, α2 Rotor relative inlet flow angle, β1 Rotor relative exit flow angle, β2 Stage reaction, λ Stage flow coefficient, φ = Vx/U Stage loading coefficient , ψ = ΔH/U**2 

Allowing all combinations of these would give too many options, so the combinations which can be used for input with FLO_TYP = “AXI” are: 

(φ, α2, β2 )  ,  ( φ, β1, β2) ,   ( λ, α1, α2)  and  (φ, ψ, λ) . 

The last combination is probably the most convenient as it allows the basic dimensionless groups which determine stage performance to be fixed, it is used with the equation 

**==> picture [128 x 18] intentionally omitted <==**

to obtain αo, the absolute flow angle at stage inlet and exit, then standard velocity triangle relationships are used to obtain the rest of the flow angles. 

Using FLO_TYP= “AXI” it is possible to design multistage machines with repeating stages very quickly by simply answering  “Y”  when asked if the velocity triangles  and design radius are the same as for the last stage.  The velocity triangles and design radius will then remain the same but the blade height will change. If the design radius is changed between two stages using FLO_TYP = “AXI” then either the change in radius must be small of the gap between stages must be large, otherwise the hub and casing stream surfaces are likely to become highly curved. If the radius change is not small then FLO_TYP = “MIX” should be used. 

The alternative, more flexible, choice for specifying the stage geometry is to input the coordinates of the design stream surface, which can include radius changes and can even be fully radial. The variation of meridional velocity ratio along this stream surface must also be specified. The meridional velocity ratio is the ratio of the local meridional velocity to that at the rotor leading edge. This option is selected by choosing FLO_TYP = “MIX” when requested on the screen. There is no assumption of a repeating stage and so 4 pieces of data are needed to specify the velocity triangles.  These can be specified either by inputting all 4 blade angles,  α1, α2, β1 and β2 or by specifying the absolute flow angles, αo, α4 , at stage inlet and outlet, together with the stage loading coefficient and flow coefficient, both defined at the rotor leading edge. The first option is chosen by setting MIXTYP = “A” , the second by MIXTYP = “B”. When MIXTYP = “A” is used the flow coefficient is obtained from the difference between the first blade exit angle and the second blade inlet angle, hence there is no direct control over the flow coefficient. e.g. for a turbine 

## φ = 1/(tan(α2) − tan(β1) ) 

For FLO_TYP = “MIX” the stream surface axial and radial coordinates are input separately for each stage and must extend from upstream of the stage to downstream of it. Typically 6 points would be sufficient to define the stream surface through a single stage. **There must be points on the stream surface at the leading and trailing edges of each blade row** and these points are numbered to define the blade positions. The stream surfaces used for input on different stages must form a **continuous smooth surface** but the input points for different stages can overlap if convenient, they are then sorted into a continuous surface by the program. 

The blade profiles are first generated on a plane x-y surface and are then transformed onto the input stream surface using 

**==> picture [80 x 36] intentionally omitted <==**

where  θ  is the circumferential angle and r the local radius.  This ensures that the angle between a local line at constant circumferential angle and the local flow direction remains unchanged and a flat plate transforms into a log spiral curve. This should ensure that the blade loading remains similar to that of a 2D blade with the same angles and same meridional velocity ratio. 

Given the inlet conditions, rotational speed, design radius, velocity triangles and a guessed efficiency the program calculates the density at each station through the machine and from that and the mass flow obtains the annulus area. The stream surface used for design can be chosen to be either the hub, casing or mid-span surface. Given the radius on the mean stream surface and the annulus area, the hub and casing radii are easily obtained. Note that if the change if annulus area across a blade row is large, then hub or casing stream surfaces, which are not the specified design surface, may become unrealistically highly curved. This is especially likely with high pressure ratio turbine stages when the hub steam surface is specified, the casing may then become unrealistic and the “stagen.dat” file should be edited to correct this. 

The velocity triangles are specified at the design radius and their variation along the span is obtained by assuming a free vortex design so that  r Vθ  = constant along the span. This should produce a flow with fairly uniform meridional velocities.  If the velocity triangles for a stage are the same as for the previous stage, that stage can be generated by simply typing ”Y”  when asked if the flow angles are the same. 

For FLO_TYP = “AXI” the blade axial chords are input as data and the inter-stage and inter-row spacings are specified as fractions of the axial chord. For FLO_TYP= ‘MIX” the leading and trailing edges, and hence the blade meridional chords and blade row spacings, are specified by the numbered input points on the stream surface. The quasi-orthogonal lines at leading and trailing edges are assumed to be straight and any taper of the axial chord is allowed for by inputting the angle between the QO lines and the axial direction, this angle will be close to 90[o] for an axial machine and close to 180[o] for a radial flow machine. 

The number of blade sections output to STAGEN is specified by default and typically 3 to 5 sections should be sufficient unless the blade is very highly twisted. The blade geometry on each of these sections is specified by the inlet and exit angles, which are available from the velocity triangles, the maximum thickness to chord ratio and the fraction of axial chord where maximum thickness occurs, which are input as data.  The blade angles are set by assuming that the tangent of the relative flow angle varies linearly with a transformed axial chord according to 

## tan(α) = tan(α1) + (tan(α2) − tan(α1)) ( _x_ / _Cx_ ) _[E]_ 

where E is an exponent which is set in the defaults and Cx is the axial chord.  E = 1 gives a linear variation in tan(α) and increasing E moves the point of maximum camber, and hence the blade loading, forwards.  Typical values of E would be 1.0 for turbines and 1.5 for compressors. The leading and trailing edge thicknesses are set as fractions of the axial chord by default values. 

The angles obtained from the velocity triangles are the flow angles and to allow for differences between the metal angles and the flow angles, the angle of incidence and of deviation can be specified for each blade row.  The deviation angles are always positive, but the incidence angles may be either positive or negative as defined in the conventional way. 

This procedure allows reasonable blade shapes to be generated but the detailed shape will usually need to be refined within STAGEN in the light of the 3D solution.  The number of blades is estimated from a specified default value of a modified Zweifel coefficient. This is modified to allow for changes in radius and in meridional velocity. Different default values are used for turbines and compressors, these can be changed if required, increase the Zweifel coefficient to increase the blade loading and reduce the number of blades. **The estimates of blade numbers are not reliable for radial flow machines** and the blade numbers for these should be estimated independently and the values in the “ **stagen.dat** ”  data set changed if necessary. 

MEANGEN will always design complete stages but not all blade rows need be output to the file “ **stagen.dat** ”, the choice of which blade rows to output is determined by the values of IFOUT, which are requested at the end of the input data. This allows single blade rows to be generated. The easiest way to generate a single blade row is to use FLO_TYP = “MIX”, MIXTYP = “A”  to generate a single stage with one of its blade rows having the required angles.  The row may be either a stator or rotor. Then set IFOUT = “Y”  for that blade row but IFOUT = “N” for the other row. The exit pressure is determined by the stage design, including the deleted blade row, and so its value may need to be changed by editing the file “stagen.dat” . 

To generate an IGV in front of a compressor stage, first generate an extra dummy stage in front of the main stages.  Use  FLO_TYP = “MIX”,  MIXTYP = “B”  for this stage and set the absolute inlet and outlet angles for the stage to be the inlet and exit absolute flow angles required from the IGV. Set the flow coefficient of the dummy stage to that required for the whole machine and set the loading coefficient to zero.  The latter ensures that the rotor of the dummy stage has no turning and does no work and so does not change the inlet stagnation temperature or flow angle. The stream surface through the dummy stage must match that for the other stages and the first stator leading and trailing edge positions on the stream surface should be those required for the IGV.  Then set IFOUT = “N” for the rotor of the dummy stage and IFOUT = “Y”  for the stator so that only the stator details are output. The other stages of the machine can be designed as usual. 

To generate an OGV for a turbine or compressor then add an extra dummy stage after the main stages. Use  FLO_TYP = “MIX”,  MIXTYP = “B”  for this stage with its inlet and outlet absolute flow angles being those required from the OGV. Set the loading coefficient of the dummy stage to zero so that its rotor does not change the outlet pressure or flow angle. The stream surface for the dummy stage must be continuous from that of the main stages. 

If the machine is a compressor set the dummy rotor leading and trailing edge points on the stream surface to be **just downstream** of the trailing edge point of the previous stage **and in front of the leading edge point required for the OGV** . The dummy rotor may be given a very small chord if necessary to satisfy this. Set the stator leading and trailing points on the stream surface to be those required for the OGV. Then set IFOUT = “Y”  for the stator (i.e. the second blade row)  and  IFOUT = “N” for the rotor (the first blade row) of the dummy stage. 

If the machine is a turbine set the stator (first blade row) leading and trailing edge points of the dummy stage to be those required for the OGV and set the dummy rotor (second blade row)  leading and trailing edge points any convenient distance downstream of these. Then set IFOUT = “Y”  for the first blade row and IFOUT = “N” for the second blade row of the dummy stage. 

## **INPUT AND OUTPUT FILES** 

When MEANGEN is started it asks whether you want to take input from the screen or from a file.  If you choose the screen then all the input is generated by typing in answers to questions on the screen. If you choose input from a file, then the file must be named “ **meangen.in** ” . 

On completion MEANGEN writes a file “ **stagen.dat** ” , which is an input file for the blade geometry program STAGEN.  STAGEN will run using “ **stagen.dat** ” without any changes to the file and will produce an input  file, “ **stage_new.dat** ”,  for the 3D solver MULTALL. However, in most cases it will be necessary to edit “ **stagen.dat** ” to make changes to the blade geometry. STAGEN also writes a file called **stage_old.dat** which is the data input to MULTALL if using the old style formatted input. 

MEANGEN also writes a file called “ **meangen.out** ” , which is a copy of the input data. To make changes to the input data, edit this file and then copy it to “ **meangen.in** ”. Then run MEANGEN with the input option chosen as a file. This is usually the easiest way to make changes to a design after the first screen input. 

## Sample Data set 

The data below shows a “ **meangen.in** ”  data set for a single stage centrifugal compressor with axial inlet and radial outlet flow. The text on the right hand side is only used to describe the data, only the numbers and first few characters on a line are actually used to generate the data. 

John Denton.  February 2017. 

## **UPDATE  3/10/2017** 

A new version  MEANGEN-17.4   has been  added. This has additions to include a blockage factor, which is sometimes used in compressors to allow for the blockage due to the growth of the annulus boundary layers. It also allows the amount of blade twist to be scaled from the free vortex value so that untwisted or over-twisted blades can be generated. In addition the blade sections can be individually rotated by an amount specified in the input data, the actual rotation is performed in STAGEN. 

Because of these additions previous MEANGEN.IN data sets are not quite compatible with version 14.4 although they can easily be updated. Three new data sets for the new version have been added to the sample data sets provided. 

C                        TURBO_TYP,"C" FOR A COMPRESSOR,"T" FOR A TURBINE MIX                      FLO_TYP FOR AXIAL OR MIXED FLOW MACHINE 287.150     1.400     GAS PROPERTOES, RGAS, GAMMA 1.000   300.000     POIN,  TOIN 1                    NUMBER OF STAGES IN THE MACHINE M                        CHOICE OF DESIGN POINT RADIUS, HUB, MID or TIP 7000.000             ROTATION SPEED, RPM 20.000             MASS FLOW RATE, FLOWIN. B                        MIXTYP = INPUT TYPE FOR FLO_TYP = "MIX" . 1.0000               FLOW COEFFICIENT AT THE FIRST ROTOR LEADING EDGE. 0.000    20.000     STAGE INLET AND OUTLET ABSOLUTE FLOW ANGLES. 5.0000               STAGE LOADING COEFFICIENT AT THE ROTOR LEADING EDGE. 11                    NUMBER OF POINTS ON THE STREAM SURFACE. THE FOLLOWING LINE OF DATA CONTAINS THE STREAM SURFACE AXIAL COORDINATES. -0.2000   -0.1000    0.0000    0.1000    0.1700    0.1900    0.1950    0.2000 0.2000    0.2000    0.2000 THE FOLLOWING LINE OF DATA CONTAINS THE STREAM SURFACE RADIAL COORDINATES. 0.2000    0.2000    0.2000    0.2200    0.3000    0.4000    0.5000    0.5500 0.7000    0.7500    0.8500 

THE FOLLOWING LINE OF DATA CONTAINS THE MERIDIONAL VELOCITY RATIOS. 1.0000    1.0000    1.0000    1.0000    1.0000    0.9000    0.8000    0.7500 0.7000    0.7000    0.6500 3    7    8    9     LEADING AND TRAILING EDGE POINTS ON THE MEAN STREAM SURFACE. N                        DO YOU WANT TO CHANGE THE STREAM SURFACE COORDINATES ? 0.800             GUESS OF THE STAGE ISENTROPIC EFFICIENCY 

5.000   5.000         ESTIMATE OF THE FIRST AND SECOND ROW DEVIATION ANGLES 

0.000   0.000         FIRST AND SECOND ROW INCIDENCE ANGLES 90.000 180.000         QO ANGLES AT LE  AND TE OF ROW 1 180.000 180.000         QO ANGLES AT LE  AND TE OF ROW 2 N                        DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N" Y                        IS OUTPUT REQUESTED FOR ALL BLADE ROWS ? N    ROTOR No.   1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 0.0500  0.3000         MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  1 0.0500  0.3000         MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  2 0.0500  0.3000         MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  3 N    STATOR No.  1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 0.0500  0.5000         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  1 0.0500  0.5000         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  2 0.0500  0.5000         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  3 



# --- END OF SOURCE: meangen-instructions.pdf ---



# ========================================================
# START OF SOURCE: Multall Tutorial 2020.pdf (Category: Multall Documentation)
# ========================================================

## Delft University of Technology 

AE4206 Turbomachinery 

**==> picture [453 x 417] intentionally omitted <==**

## **Assignment software tutorial** 

_Author:_ E. C. Bunschoten 

February 29, 2020 

## **1 Introduction** 

This tutorial contains some basic instructions on how to use Meangen, Stagen and Multall to analyze the performance of an axial compressor. Many of the instructions listed in this document can however also be used for different machine types. In this project, it’s required to perform a CFD analysis of the first stage of a compressor. In Figure 1.1, an example workflow process can be seen on how the teams are to perform this analysis and end up with a satisfactory design. 

**==> picture [453 x 178] intentionally omitted <==**

Figure 1.1: Workflow process of performing the CFD analysis 

In block 0, the conceptual design process takes place, where based on the compressor requirements, you calculate the desired set of duty coefficients and geometry of the compressor by performing meanline calculations and predicting the losses with knowledge obtained in the lectures and other sources. Once the preliminary design has been chosen, the detailed design phase can start, in which the CFD analysis takes place. 

The first step is by using a program called Meangen. Meangen generates the compressor geometry based on the input resulting from the preliminary design. You can compare this geometry with the one you predicted during the conceptual design phase to verify your approach. Meangen puts out more detailed data on the metal angles of the blades and thickness distribution. In block 2, called Stagen, input from Meangen is used to generate the outline of the blades, which can then be inspected using TecPlot. Stagen also provides the input data for the CFD analysis, including the mesh, maximum number of iterations and convergence criteria. The CFD analysis itself is then initiated in block 3 by a program called Multall. The outputs from multall include the total mass flow, machine power and the flow field itself. The latter can be inspected in detail using TecPlot. 

1 

## **2 Using Meangen** 

In this chapter, the first steps of the machine analysis are described. Before being able to do a detailed analysis of the flow within the machine, you of course need a machine geometry. This is what Meangen is used for. Meangen is essentially a **meanline design program** . From a set of duty coefficients, mass flow rate, number of stages and the stage power, Meangen constructs the meridional flow path of the machine. Note that Meangen **does not apply any loss model** , so you’ll have to calculate the stage loss coefficients yourself in order to predict the machine efficiency. It’s important you do this before doing the detailed analysis, as the flow channel produced by meangen will probably be too narrow for the design mass flow when assuming an isentropic machine. 

For Meangen to function, you will need the Meangen.exe executable and the input file Meangen.IN. Meangen.IN contains all the instructions and data Meangen needs to construct the meridional flow path. Once you have downloaded the executables, you can use them by opening a command window, navigating to your destination folder(or do this using _system_ and _sprintf_ in Matlab for example) and using the following command. 

**==> picture [320 x 11] intentionally omitted <==**

Meangen then asks whether the instructions should be collected from an input file or are to be filled in on the screen. If you have an input file prepared and in the current directory, you can type ”F” and Meangen will generate the design automatically. If you want to follow the same design approach as given in the example file, you can use this method right from the start. In case you like to take a different approach/analyze more stages, it might be more beneficial to type ”S” and fill in your design parameters using the command window. Meangen generates a meangen.OUT file, in which all instructions you put in are listed, which you can use as an input file for your next design. In Figure 2.1, the meangen.OUT file from the design example can be seen. The design inputs are on the left and the description of the parameter on the right. Next up follows a step-by-step description of the Meangen inputs. 

**==> picture [363 x 246] intentionally omitted <==**

Figure 2.1: meangen.OUT file from the example 

1. On the first line, it asks for the machine type, being a compressor(”C”) or a turbine(”T”). The second line specifies whether this is an axial(”AXI”) or mixed flow(”MIX”) machine. 

2 

_CHAPTER 2. USING MEANGEN_ 

2. The next two lines ask for the gas properties(gas constant and specific heat ratio) of the working fluid and the inlet total pressure in bar and the inlet total temperature in Kelvin. 

3. On line 5, you specify the number of stages to be produced by Meangen. 

4. On line 6, Meangen asks for hub, mid or tip based design. This means that Meangen will keep the given radius constant over the stage. So in this case(”M”), meangen will keep the mean radius of the rotor and stator of this stage constant. 

5. The next two lines ask for the rotation speed and machine mass flow rate in kg s _[−]_[1] . 

6. Next, Meangen asks for how you’d like to define the velocity triangles of this stage. With option ”A”, you insert the degree of reaction, flow coefficient and loading coefficient. Option ”B” allows you to specify the flow coefficient, stator exit angle and rotor exit angle(relative). With option ”C”, you specify the flow coefficient and relative rotor inlet and exit angle. Finally, option ”D” asks for stage reaction and first blade row inlet and exit angle. 

7. The next part has to do with the calculation of the machine design radius. This can be done by inserting the design radius directly(option ”A”) or by inserting the stage enthalpy change in kJ kg _[−]_[1] (option ”B”). 

8. On lines 13 and 14, the axial chord lengths and row and stage gaps are specified. The first value for axial chord represents the first blade row chord and the second value the second blade row. After this, the row gap(space between the rotor and stator) and stage gap(space between this and following stage) are specified. These are taken as a fraction of the stage first blade row chord(so in this case the rotor chord, resulting in a row gap of 0 _._ 01 m and a stage gap of 0 _._ 02 m). 

9. Next, Meangen asks for the blockage factors at the first blade row leading edge and second blade row trailing edge. The blockage factor is the ratio between the local boundary layer displacement thickness and the blade height. Meangen uses these values to scale up the machine sufficiently in order to allow for the required mass flow to flow through. 

10. On the next line, Meangen asks for a guess of the isentropic efficiency of the stage. Meangen will use this to calculate the pressure at the end of the stage and size the exit blade height appropriately. 

11. The next two lines have to do with the incidence and deviation angles of the blade rows. On the first line, the deviation angles of the rotor and stator rows are to be filled in and on the second line the incidence angles. In Figure 2.2, once can see the definition of the incidence and deviation angles. Meangen will add these angles to the inflow/outflow angles resulting from the set of duty coefficients of the blade row in order to produce the blade metal angles. 

12. On line 19 of Figure 2.1, the blade twist option is specified. This has to do with the level of vortex-free design of the stage. Filling in 1.0 results in the blade to yield full vortex-free design and 0.0 leads to a prismatic blade. The user can also fill in a value in between 1.0 and 0.0 in order to for instance go for a controlled-vortex design. The mathematical law for this is 

**==> picture [406 x 28] intentionally omitted <==**

Here, _β_ is the relative blade angle (or absolute in case of a stator), _T_ the fractional twist input value, _β_ design the blade angle of the design section(depending on your input for hub, 

3 

_CHAPTER 2. USING MEANGEN_ 

mean or tip design). _r_ design is the radius of the design section and _r_ the radius of the local section. _phi_ ( _r_ ) is the local flow coefficient, equal to _φ_ design _r_ desi _r_ gn in case axial velocity is assumed constant over the blade span. In Figure 2.4, the blade sections at the hub, mid and tip of a turbine stage can be seen for twist values of 0.5 and 

13. For the next input, the user gets the option to change the blade angles later in case the resulting stage geometry is not as desired. This is only really useful when using the screen approach when using Meangen, as the user gets updated on the machine design after filling in certain design parameters. When using an input file for the Meangen commands, it’s advised to just fill in ”N” at this option. 

14. The next input has to do with the taper and sweep of the blade rows. The user is asked to fill in the QO angles at the leading and trailing edge of the first and second blade row. In Figure 2.3, an illustration is provided of the meaning of these angles, where Q1 and Q2 are the respective leading and trailing edge QO angles. If the user were to fill in 90 degrees for all QO angles, both blade rows would consist of blades with a taper ratio of 1.0. 

15. The next input is again a choice for the user to change the flow angles for the current stage and is only relevant when filling in the design parameters on screen. 

16. The next option on line 24 is important to write ”Y”, as it will write the Stagen files for all blade rows, which will have to be used later during the CFD analysis. 

17. The last two inputs have to do with the thickness distribution over the blade surface. By filling in ”N” on lines 25 and 29, the user gets the option to change the thickness-tochord ratio and chordwise location of maximum thickness on the blade on the root(section 1), mid(section 2) and tip(section 3) of the blade row. The first column represents the thickness-to-chord ratio and the second column the location of maximum thickness. 

**==> picture [272 x 232] intentionally omitted <==**

Figure 2.2: Blade incidence and deviation angle definition 

4 

_CHAPTER 2. USING MEANGEN_ 

**==> picture [272 x 158] intentionally omitted <==**

Figure 2.3: Blade QO line angles 

**==> picture [363 x 292] intentionally omitted <==**

Figure 2.4: Spanwise profile variation with twist value 

After filling in all design parameters and initiating Meangen, a meangen.OUT, meandesign.OUT and stagen.dat file are created. In meangen.OUT, all commands you inserted can be found as how they were interpreted by Meangen. If there are differences between the meangen.OUT and the meangen.IN file you used, you probably inserted a command the wrong way. meandesign.OUT contains a more detailed description of the machine geometry, flow deflection angles and flow properties along the mean line. stagen.dat contains the information on the blade profiles, which can be loaded into TecPlot for inspection. 

5 

## **3 Using Stagen** 

In this chapter, a brief tutorial is given on how to use Stagen and how to use it to adjust the convergence criteria and iteration count for Multall. After using Meangen to generate a meanline design and preliminary geometry, Stagen is used to generate a suitable mesh for the CFD analysis in Multall. This is done by opening a command window, navigating to your current directory(where you have stored the output files from Meangen) and typing the following command: 

**==> picture [319 x 12] intentionally omitted <==**

The message will then appear, asking for whether the Stagen input file is called ”stagen.dat”. This is the case by default, so after you type ”Y”, Stagen will read the stagen.dat file generated by Meangen earlier. 

Stagen then produces 4 files. _stage_ ~~_n_~~ _ew.dat_ contains all inputs Multall requires to function. This file has to be used for subsequent steps. Stagen also creates a file named _stage old.dat_ . This input file is compatible with older versions of Multall, but is not compatible with the version you’ll be using during the project. _blade_ ~~_p_~~ _rofiles.tec_ contains the blade profiles in a format which can be read by Tecplot. _stagen.out_ lists the blade profile coordinates, in case you’d like to plot them using a program other than Tecplot. 

In order to inspect the blade profiles in Tecplot, download and install Tecplot 360 from the student software resources portal, open it and load the _blade_ ~~_p_~~ _rofiles.tec_ file. On the left bar, click on the ”Mapping Style” button to select the blade profiles you want to inspect. 

**==> picture [148 x 147] intentionally omitted <==**

Figure 3.1 

The following window then appears, in which you can select which curves you want to see(YUP is upper curve, YLOW lower curve and THICK the blade thickness) and which blade and section under the ZONE tab(section 1, 2 and 3 are hub, mean and shroud sections respectively). 

6 

_CHAPTER 3. USING STAGEN_ 

**==> picture [430 x 197] intentionally omitted <==**

Figure 3.2 

The plotted blade profile should look something like the one shown in Figure 3.3, where the red line, green line and blue line are the upper, lower and thickness curves respectively. 

**==> picture [453 x 366] intentionally omitted <==**

Figure 3.3 

During detailed design, you might want to adjust certain aspects of the blade shape to increase performance. These can be adjusted in _stagen.dat_ for each blade and its respective sections. In 

7 

_CHAPTER 3. USING STAGEN_ 

Figure 3.4, the line defining the blade profile specifications for section 1 of the rotor blade row is highlighted. 

**==> picture [453 x 211] intentionally omitted <==**

Figure 3.4: Section from _stagen.dat_ , highlighting the line defining blade profile specifications 

The first two numbers represent the leading edge and trailing edge thickness ratio( _c[t]_[).][The third] and fourth numbers represent the maximum thickness-to-chord ratio and its chordwise location respectively. These values were defined at the last couple of commands in Meangen, but can be changed here if desired. The two numbers after those represent the length of the leading and trailing edge. High numbers translate to a more sharp edge, while low numbers result in more rounded edges. This is illustrated in Figure 3.5, where on the left, 0.1 is used as the leading edge length, while on the right 0.01 was used. 

**==> picture [453 x 170] intentionally omitted <==**

Figure 3.5: Comparison between high and low leading edge length parameter 

The final number has to do with the flatness of the thickness profile. High numbers result in a very flat profile, where the blade thickness retains its maximum thickness for most of the blade length, while low numbers result in a more diamond-type shape. In Figure 3.6, the effect of changing the flatness parameter is shown. On the left, a blade profile with a high number(5.0) is shown and on the left a blade with a low number(1.0). 

8 

_CHAPTER 3. USING STAGEN_ 

**==> picture [453 x 225] intentionally omitted <==**

Figure 3.6: Comparison between high and low flatness parameter 

There are more parameters which can be adjusted in the subsequent lines, but the ones shown in this chapter were deemed the most influential. Before starting the CFD analysis in Multall, you can adjust the maximum number of iterations and the convergence criterion. Unfortunately, this isn’t as straightforward as changing the blade shape. In order to adjust these parameters, one has to adjust the source code of Stagen itself. When opening the source code in for instance Notepad++, the Multall control variables can be found between line 166 and 232. NMAX on line 170 represents the maximum number of iterations. Once this iteration count is reached, Multall will finalize its calculations and write its results, irrespective of the current convergence. The convergence limit is called CLIM and can be found on line 227. When the convergence factor gets below this number, Multall will again put out its results. 

Stagen is written in Fortran and in order to compile it into a functional executable, you need a Fortran compiler such as G95. Once you have this program installed, open a command window, navigate to the folder where the source code is kept and then type _G95 stagen-17.2.f_ . The new executable is then created in the current folder. By then replacing the Stagen executable in your executable folder with the new one, Stagen will put out the adjusted settings as input for Multall. 

9 

## **4 Using Multall and Tecplot for postprocessing** 

After Stagen is done, the CFD analysis in Multall can start. In order to initiate Multall, open a command window, navigate to the folder where _stage new.dat_ is stored and type the following command: 

**==> picture [388 x 12] intentionally omitted <==**

The last part of the command transfers all result data to the file _results.txt_ . You can also leave this out. In that case, all the outputs from Multall will be displayed in the command window. By reloading the _results.out_ , you can check on progress. Solving the flow field can take a long time, so don’t be surprised if it takes half an hour or more! 

In case you’d like Multall to stop and put out the results up to now, open the _stopit_ file, which was made when initiating Multall in your current folder. Open this file in a text editor and replace the 0 with a 1. Multall will read this and terminate the solving process. To inspect the flow field and extract important flow parameters, you will have to convert the field data to a format readable by Tecplot. This can be done by executing the following command in the command window. 

**==> picture [329 x 11] intentionally omitted <==**

The program will ask how many blade passages you want to show. 3 or 4 should be enough to properly show the flow field. Any higher will generate huge data files and take forever to load. After the data is converted, open Tecplot and load the _tecplot-input.dat_ file. This will again take a few minutes to load. After Tecplot has finished loading, tic the ”Contour” box on the left to show the flow field. This can be seen in Figure 4.1. 

10 

_CHAPTER 4. USING MULTALL AND TECPLOT FOR POSTPROCESSING_ 

**==> picture [363 x 322] intentionally omitted <==**

Figure 4.1: Axial velocity contour of the first stage 

You can show different flow properties by clicking on ”Details” behind the Contour box. You can visualize slices of the flow field by selecting ”Slices” and selecting the flow property you want to show under ”Contour”. Below, the K-slice 19 with stagnation pressure contours. 

11 

_CHAPTER 4. USING MULTALL AND TECPLOT FOR POSTPROCESSING_ 

**==> picture [363 x 318] intentionally omitted <==**

Figure 4.2: Blade plane showing stagnation pressure contours 

Within Tecplot, you can define variables, equations and perform integrals, which you can use to distinguish 2D and 3D losses or compute efficiencies. 

12 



# --- END OF SOURCE: Multall Tutorial 2020.pdf ---



# ========================================================
# START OF SOURCE: Multall Tutorial 2021 (including TecPlot).pdf (Category: Multall Documentation)
# ========================================================

**==> picture [125 x 540] intentionally omitted <==**

## Multall 

## turbomachinery design tutorial 

Pedro Garcia Gonzalez (P.GarciaGonzalez-1@student.tudelft.nl) Matteo Pini 

Acknowledgements: John Denton, Antonio Rubino, Peter Onodi, Pablo Garrido. 

1 

**==> picture [125 x 540] intentionally omitted <==**

## Overview 

- The **Multall-open** software package is an open-source code for turbomachinery design based on the 3D, multistage, Navier-Stokes solver Multall. 

- User manuals, documents on theoretical background are available on Brightspace. 

- • This document includes information on the installation and use of the software, as well as some examples. 

- Additional notes are included below the slides, marked with an asterisk (*) 

2 

**==> picture [125 x 540] intentionally omitted <==**

## Multall Turbomachinery Design 

- The design software consists of 3 programs: 

   - Meangen – Meanline design 

   - Stagen – Geometry generation and meshing 

   - Multall – CFD 

- Source code, executables and manuals are available on Brightspace (AE4206 Turbomachinery – Content > Software). 

- Additional information, as well as a link to all the previous versions can be found here: 

- https://sites.google.com/site/multallopen/ 

3 

MEANGEN Performs a 1D calculation to obtain the velocity triangles. Sets the annulus boundaries. Generates initial blade shapes and twists them for a free vortex design. Writes an input file for STAGEN. 

**==> picture [321 x 92] intentionally omitted <==**

STAGEN Refines the blade shapes. Stacks them and combines them into stages. Writes an input file for MULTALL MULTALL Performs a 3D multistage calculation to predict the detailed flow pattern and overall performance. 

Source: Denton: _J. Denton_ : MULTALL – AN OPEN-SOURCE, CFD BASED, TURBOMACHINERY DESIGN SYSTEM 

**4** 

**==> picture [125 x 540] intentionally omitted <==**

## Data exchange with meanline design performed elsewhere 

**==> picture [514 x 411] intentionally omitted <==**

**----- Start of picture text -----**<br>
Multall-open software package<br>Basic blade geometry,<br>Meshing rules<br>Ψ,λ,γ<br>η à stagen.out – blade coord.<br>Your  own<br>meanline  design<br>(MATLAB, Excel,<br>Python,…)<br>**----- End of picture text -----**<br>


5 

**==> picture [125 x 540] intentionally omitted <==**

How to install Multall-open software package 

6 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on Windows-based machines 

1. Download the software as FORTRAN (.f) files. 2. Follow the steps of the MinGW-gfortran.pdf (available in this folder) to install the gfortran compiler on your command line. 

3. Open the meangen-17.4.f, stagen-18.1.f and multall-open-20.9.f files with a text editor, search for _dev/tty_ and comment the line that includes it by adding _**!**_ to the line. E.g.: !OPEN(UNIT=5,  FILE= '/dev/tty’) 

4. Open the commall-open-20.9 file with a text editor and change the value marked in red in the first lines to around 30 (Windows presents a memory limitation, this number should not be higher than a certain limit)*: PARAMETER(ID=30,JD=2500,KD=30,MAXKI=82,NRS=21,I G1=32,&JG1=1000,KG1=41) 

7 

**==> picture [125 x 540] intentionally omitted <==**

- Install Multall-open software on Windows-based machines 

   1. Navigate to the folder in which you have the software (Multall\Source) using cd in the command line. 

2. Type the following (in different lines): gfortran meangen-17.4.f -o meangen-17.4.exe gfortran stagen-18.1.f -o stagen-18.1.exe gfortran multall-open-20.9.f -o multall-open-20.9.exe 3. The executable files should appear in the folder in which the .f files are. 

4. If there is no _intype_ file, create one and write _N_ on it. 

5. Check the correct operation of the software using the test cases. 

8 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on macOS/Linux-based machines (1) 

- First of all, you’ll need to have installed Fortran on your machine. 

`o` For macOS: 

1. Install Xcode (available here https://itunes.apple.com/us/app/xcode/id497799835?mt=12) 

2. Install the Xcode command-line tools 

   - Open Terminal (Applications > Utilities > Terminal) and type **xcode-select --install** press Enter and follow the dialog boxes. 

3. Download and install Gfortran (from https://github.com/fxcoudert/gfortran-for-macOS/releases). Select the version based on your macOS release! 

`o` For Ubuntu: 

1. Open Terminal and type **sudo apt-get install gfortran** and press Enter. 

9 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on macOS/Linux-based machines (2) 

- Now, we need to compile the files ( _meangen-17.4.f_ , _multall-open-17.5.f_ and _stagen-17.2.f_ , located in the “ _Source code_ ” folder)  and create executables: 

   1. Open Terminal. 

   2. Navigate to the folder where the .f files that you want to compile are located by using the **cd** command followed by the path, and press Enter: 

**==> picture [303 x 26] intentionally omitted <==**

3. Once you are in the correct path, you can compile the .f file by using the following command: **gfortran -o meangen-17.4.exe meangen-17.4.f** 

**==> picture [410 x 14] intentionally omitted <==**

   4. After a few seconds, a new file (.exe) will appear in the folder where the .f file was located. 

   5. In order to execute this file, **you need to run it from the command window (Terminal)** . You can do this by dragging and dropping the .exe file to the Terminal window and pressing Enter or alternately by typing manually the path of the executable: 

- The steps followed can be repeated for the other files ( _multall-open-17.5.f_ and _stagen-17.2.f_ ), where the Folder and File names in steps 2 and 3 will need to be changed accordingly, 

10 

**==> picture [125 x 540] intentionally omitted <==**

## Meangen 

1. Run meangen-17.4.exe by double-clicking on the file. The following message should appear. 

**==> picture [300 x 196] intentionally omitted <==**

2. If answer S, the software will ask you to provide all the design parameters in the command line. 

3. If answer F, type the name of your own generated .in file, a text document with all the required design parameters (see next slide, recommended method). 

11 

**==> picture [125 x 540] intentionally omitted <==**

Meangen - Input example 

} type of machine („MIX” also for radial) 

**==> picture [370 x 48] intentionally omitted <==**

Dispacement body (boundary layer) If n, properties can be specified For each blade row separately 

12 

**==> picture [125 x 540] intentionally omitted <==**

## Stagen 

- Usage: double-click on stagen-18.1.exe 

   - Input: stagen.dat (output from Meangen). 

   - Output: `stage_new.dat` (and `stage_old.dat` ) 

   - The _intype_ file has to be set up to _N_ for the use of stage_new.dat. 

13 

**==> picture [125 x 540] intentionally omitted <==**

## Multall 

Settings related to turbulence model, fluid model, CFL number and other simulation parameters may be changed by modifying stagen_new.dat 

- Cp and gamma based on flow properties. 

- CFL number for CFD simulations. 

- NSTEPS_MAX determines the maximum number of iterations. 

- CONLIM determines the convergence of the simulation (default value of 0.1%). 

- Mesh size: IM, KM ( **have to be lower than ID, KD defined in commall-open-20.9 during the installation procedure** ). 

14 

**==> picture [125 x 540] intentionally omitted <==**

## Multall - run 

- To run the solver in cmd and save the results to file: 

```
>> multall-open-20.9.exe <
```

`stage_new.dat > results.txt` (This is one line!) 

15 

**==> picture [125 x 540] intentionally omitted <==**

## Convergence 

- Maximum iteration, convergence limit : 

- (default is 0.1%) in `stage_new.in` 

**==> picture [345 x 54] intentionally omitted <==**

- To stop a running simulation prematurely (and still save the results): 

   - Open „stopit” file 

   - Change 0 to 1 

16 

**==> picture [125 x 540] intentionally omitted <==**

## Plotting programs 

- **histage** : Program to plot out the convergence history of a MULTALL calculation. 

- **- 17.x:** 

- **plotall** Main plotting program for the output from MULTALL. 

- **:** 

- **Globplot** 

- Program for plotting out one dimensional mass averages of t he flow quantities against meridional distance. 

- **convert-to-tecplot** – Converts the Multall mesh and flowfield output to the Tecplot format. 

- **Tecplot** can be used instead of plotall for postprocessing. 

17 

## Plotting programs - plotall 

- Command line program to plot 2D sections 

**==> picture [434 x 317] intentionally omitted <==**

18 

**==> picture [125 x 540] intentionally omitted <==**

## Plotting programs - globplot 

- Plots 

- Mass flow, p*, T*, angular momentum, entropy 

**==> picture [429 x 302] intentionally omitted <==**

19 

## Plotting programs - histage 

**==> picture [304 x 391] intentionally omitted <==**

- Convergence history – mass flow, inbalance, RMS 

- Continuity error: inflow and outflow difference 

- RMS – Root mean square 

- Computation stops based on imbalance (continuity error) criteria 

- • RMS should be in order of 10^-4 to 10^-6 

20 

**==> picture [125 x 540] intentionally omitted <==**

## Postprocessing - Tecplot 

- Installation: 

   - Download from or tecplot.com 

   - TU Delft software repository (https://software.tudelft.nl/431/) 

- License activation: 

   - After starting Tecplot select License options: Network License Server 

   - FlexLM license server : flexserv4.tudelft.nl 

   - FlexLM license port : 27099 

   - It works on the campus network or with VPN connection 

21 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot – convert-to-tecplot 

- Converts CFD output to Tecplot format 

- `flow.out + grid.out` à `tecplot-input.dat` 

• In `convert-to-tecplot.f` : 

– Changing the memory allocation according to mesh size might be necessary (similarly as in Multall): 

**==> picture [569 x 61] intentionally omitted <==**

22 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot 

- Select “Tecplot Data Loader” 

**==> picture [159 x 115] intentionally omitted <==**

- If file has invalid values (NaN, Inf) it will not load it: 

- In this case go to the previous slide and change array size in the source code. 

23 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot 

- Adding an equation to compute a new 

   - variable: 

- Data à Alter à Specify equation* 

**==> picture [295 x 291] intentionally omitted <==**

- New equation: 

24 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot – line plot 

- To make a pressure coefficient plot: 

- https://www.youtube.com/watch?v=WHM 50EvKpxY 

25 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot results mesh 

**==> picture [302 x 268] intentionally omitted <==**

- 2 stage mixed flow compressor 

**==> picture [265 x 236] intentionally omitted <==**

26 

**==> picture [125 x 540] intentionally omitted <==**

## Tecplot results – contour plots 

## • 2 stage mixed flow compressor 

**==> picture [268 x 238] intentionally omitted <==**

**==> picture [273 x 242] intentionally omitted <==**

27 

Tecplot results – contour plots 

**==> picture [191 x 170] intentionally omitted <==**

## • Centrifugal compressor 

**==> picture [377 x 336] intentionally omitted <==**

**==> picture [244 x 216] intentionally omitted <==**

28 

## Tecplot results – contour plots 

- Centrifugal turbine 

**==> picture [349 x 310] intentionally omitted <==**

**==> picture [233 x 208] intentionally omitted <==**

**==> picture [232 x 206] intentionally omitted <==**

29 

**==> picture [125 x 540] intentionally omitted <==**

# **Design example 1** Design of first stage of HPC for NASA E3 engine (last year’s project) 

**30** 

## Design specifications 

|**Specification**|**Value**|
|---|---|
|Inlet total pressure (Pa)|276000|
|Inlet total temperature (K)|340|
|Overall pressure ratio|14|
|Mass flow rate (kg/s)|88.23|
|Rotational speed (rpm)|13177|
|1st stage inlet corrected tip speed (m/s)|379.5|
|IGV|No|



31 

## Steps 

## **The first step is to modify the inputs in the meangen.in file:** 

1. Write the parameters that are already known from the design specifications (e.g. inlet total temperature and pressure). 

2. Select the number of stages considering constant work per stage. _Hint: Consider reference values for maximum stage pressure ratio (around 1.6) and maximum flow deflection to avoid separation._ 

3. Select load coefficient, flow coefficient and degree of reaction based on design criteria. 

4. Compute design point radius based on continuity equation. 5. Select axial chords based on selected solidity. 

6. Provide estimates for row and stage gaps, and of blockage factors due to boundary layer. 

7. Provide an estimated of the stage isentropic efficiency based on empirical data (e.g. Smith chart) or calculations (e.g. loss models). 

8. Provide estimates of deviation and incidence angles based on models (e.g. Traupel, Greitzer, Ainley & Mathieson…). 

9. Provide taper if desired (QO angles). 

10. First estimate of blade max thickness and location (can be changed in Stagen). 

32 

Steps 

**==> picture [720 x 389] intentionally omitted <==**

33 

## Steps 

**Run meangen-17.4.exe, selecting input from file (write F in cmd). Outputs:** 

- meangen.out: slight modifications from meangen.in (e.g. number of decimals), check if the values are roughly the same). 

- stagen.dat: inputs for Stagen. 

**Modify stagen.dat (make changes on local blade profile characteristics based on fluid-dynamic understanding of turbomachinery behaviour, loss models, and the indications provided in the tutorial by Denton in the appendix of this ppt):** 

1. Change IM, KM to a value lower than the limit defined in commall. 

2. Change NPOINTS to perform grid convergence study (the higher the number, the higher the accuracy of CFD results, but the higher the computational time). _See the tutorial by Denton in the appendix for more information._ 

3. Number of blades can also be modified if the solidity estimate does not lead to satisfactory results. 

4. Change detailed profile characteristics (see next slides). 

34 

## Steps 

**==> picture [715 x 374] intentionally omitted <==**

35 

## Steps 

**==> picture [682 x 387] intentionally omitted <==**

36 

## Steps 

**==> picture [661 x 368] intentionally omitted <==**

37 

## Steps 

**==> picture [666 x 373] intentionally omitted <==**

38 

## Steps 

**==> picture [663 x 371] intentionally omitted <==**

39 

## Steps 

**==> picture [717 x 372] intentionally omitted <==**

40 

## Steps 

**==> picture [694 x 371] intentionally omitted <==**

41 

## Steps 

## **Run stagen-18.1.exe. Write the name of your file in the cmd. Outputs:** 

- stagen.out: blade profile coordinates. 

- blade_profiles.tec: blade profiles in format readable by Tecplot. 

- stage_new.dat: inputs for Multall. 

- stage_old.dat: inputs for old version of Multall. 

## **Change parameters of CFD simulation if necessary:** 

1. Cp and gamma have been defined in meangen.in, check if correct. 

2. CFL number to ensure convergence of CFD simulations. 

3. Maximum Mach number is defined as MACHLIM. 

4. Convergence parameters as defined as the maximum number of steps (NSTEPS_MAX) and the convergence parameter (CONLIM), which are given standard values of 9000 and 0.1%. 

5. IM and KM can again be changed in this file. 

42 

## Steps 

**Run Multall by the following command in cmd (after cd-ing to the folder):** `multall-open-20.9.exe < stage_new.dat > results.txt` 

## **Wait until the simulation has converged (can take several minutes).** 

**. Check convergence with** _**histage**_ 

## **For postprocessing:** 

1. Convert results using _convert-to-tecplot.exe_ using 1-2 blade passages _._ This will make a Tecplot input file from the flow_out and grid_out files. 

2. Open the tecplot-input.dat file in Tecplot. 

3. Obtain the distribution of different properties in Details, behind the Contour box. A certain flow slice can be selected. 

4. Equations can be defined to obtain the desired parameters and compute losses. 

43 

## Steps 

**==> picture [385 x 540] intentionally omitted <==**

44 

## Steps 

**==> picture [342 x 350] intentionally omitted <==**

## **Mach number distribution** 

**==> picture [374 x 428] intentionally omitted <==**

**Total pressure distribution along radius (shockwave formation seen close to tip)** 

45 

## Steps 

## • Comparison of results: 

|**Parameter**|**Unit**|**Meanline**|**CFD**|
|---|---|---|---|
|**Total-to-total efficiency**|%|91.2|88.8|
|**Mass flow rate**|kg/m^3|88.23|88.13|
|**Pressure ratio**|-|1.6|1.59|



- Check if target efficiency, required mass flow rate and pressure ratio are achieved. 

46 

# **Design example 2 3-stage axial turbine** 

**47** 

**==> picture [125 x 540] intentionally omitted <==**

## Example: 3-stage axial turbine 

- This example shows the steps from the end of a preliminary design until CFD calculation and postprocessing and evaluating the results 

- The following preliminary design results are given: 

||**Unit**|**Value**|
|---|---|---|
|Inlet total pressure|bar|2|
|Inlet total temperature|K|500|
|Blade twist||Free vortex|
|Hub radius (const.)|m|0.4|
|Target total-to-total<br>efficiency|%|90|
|Mass flow rate|kg/m^3|25|
|Rotation speed|RPM|3000|
|Degree of reaction|-|0.25|
|Flow coefficient|-|0.5|
|Work coefficient|-|2|



• Same flow coefficient, load coefficient and degree of reaction is used for all stages. 

48 

**==> picture [125 x 540] intentionally omitted <==**

Example: 3-stage axial turbine 

- Blade chords are selected based on the calculated blade span and by selecting a proper aspect ratio. 

- Row gaps are selected 

- Incidence and deviation angles, blade thickness ratios and blockage factors are estimated 

- From the preliminary calculations and design choices the Meangen input file* is constructed à 

49 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Meangen Meangen input file (name the file `meangen.in` ):* 

**==> picture [540 x 405] intentionally omitted <==**

**----- Start of picture text -----**<br>
||||
|---|---|---|
|T                        TURBO_TYP,"C" FOR A COMPRESSOR,"T" FOR A TURBINE|
|AXI                      FLO_TYP FOR AXIAL|OR MIXED FLOW MACHINE|
|287.500     1.400     GAS PROPERTOES, RGAS, GAMMA|
|2.000   500.000     POIN,  TOIN|
|3                    NUMBER OF STAGES IN THE MACHINE|
|H                        CHOICE OF DESIGN POINT RADIUS, HUB, MID or TIP|
|3000.000             ROTATION SPEED, RPM|
|25.000             MASS FLOW RATE, FLOWIN.|
|A                        INTYPE, TO CHOOSE THE METHOD OF DEFINING THE VELOCITY TRIANGLES|
|0.250  0.500  2.000    REACTION, FLOW COEFF., LOADING COEFF.|
|A                        RADTYPE, TO CHOOSE THE DESIGN POINT RADIUS|
|0.400|THE DESIGN POINT RADIUS|
|0.050       0.040 BLADE AXIAL CHORDS IN METRES.|
|0.250       0.500 ROW GAP  AND STAGE GAP (fractions)|
|0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE|
|0.900             GUESS OF THE STAGE ISENTROPIC EFFICIENCY|
|1.000   1.000         ESTIMATE OF THE FIRST AND SECOND ROW DEVIATION ANGLES|
|-2.000  -2.000         FIRST AND SECOND ROW INCIDENCE ANGLES|
|1.00000|BLADE TWIST OPTION, FRAC_TWIST|(1 is free vortex, 0 is without twist)|
|n                        BLADE ROTATION OPTION , Y or N|
|92.000  88.000         QO ANGLES AT LE  AND TE OF ROW 1|
|88.000  92.000         QO ANGLES AT LE  AND TE OF ROW 2|
|n                        DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"|
|y                        IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE INPUT TYPE AND VELOCITY TRIANGLES, SET = "C" TO CHANGE|
|INPUT TYPE.|
|0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE|
|n                        DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"|
|y                        IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE INPUT TYPE AND VELOCITY TRIANGLES, SET = "C" TO CHANGE|
|INPUT TYPE.|
|0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE|
|n                        DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"|
|Y                        IS OUTPUT REQUESTED FOR ALL BLADE ROWS ?|
|N    STATOR No.  1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|
|0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  1|
|0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  2|
|0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  3|
|Y    ROTOR No.   1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|
|Y    STATOR No.  2 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|
|Y    ROTOR No.   2 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|
|Y    STATOR No.  3 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|
|Y    ROTOR No.   3 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE|

**----- End of picture text -----**<br>


50 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

• Before starting the calculations make sure to have all of the following files in the same folder: 

**==> picture [538 x 204] intentionally omitted <==**

51 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

- Run _Meangen_ in the command line with the input file ( `meangen.in` ). `>>Meangen17.4.1.exe` 

- Press „F” to input the data* from file 

- This generates the input file for Stagen (next slide) 

52 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

## • _Meangen_ ouputs 3 new files: 

   - `meandesign.out` – row geometry & thermodynamics 

   - `meangen.out` – echo of the Meangen input file 

   - `stagen.dat` – Stagen input file 

- meandesign.out includes thermodynamic properties, geometry and the data for velocity triangles for each blade row: 

```
STAGE No, ROW No, No. BLADES 1 1 33
STAGE No, ROW No, No. BLADES 1 2 71
```

```
*****************************************************
CONDITIONS FOR THE FIRST BLADE ROW OF THE STAGE.
THIS IS A TURBINE STATOR
```

```
*****************************************************
FIRST BLADE INLET AND EXIT ANGLES  -26.565073
74.054665
```

```
FIRST BLADE AXIAL VELOCITY      62.8318
FIRST BLADE INLET MACH NUMBER   0.15697631
FIRST BLADE EXIT MACH NUMBER    0.52361447
FIRST BLADE EXIT DENSITY        1.201726
FIRST BLADE EXIT PRESSURE       1.6376798
FIRST BLADE INLET STAGN PRESS   2.0000002
FIRST BLADE EXIT STAGN PRESS    1.9741219
FIRST BLADE REL INLET STAG PRES 2.0000002
FIRST BLADE EXIT TEMPERATURE    474.00806
FIRST BLADE EXIT STAGN TEMP     500.
FIRST BLADE TIP RADIUS =        0.5021015
FIRST BLADE INLET SPAN =        0.107626915
FIRST BLADE AXIAL CHORD=        0.05
FIRST BLADE ASPECT RATIO =      2.1525383
```

```
…
```

53 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Meshing 

- In `stagen.dat` the mesh size can be changed*: 

```
287.5000      1.4000 GAS CONSTANT, GAMMA
37        37     IM, KM
1.2500     20.0000  FPRAT,  FPMAX
1.2500     20.0000  FRRAT,  FRMAX
0               IFDEFAULTS
6         3     NOWS, N SECTIONS
1.000               SCALING FACTOR
```

- Run Stagen. This generates the mesh `>>Stagen17.2.2.exe` 

- Answer with yes (y) for the question about the input file name 

- _Stagen_ will produce the following files: 

   - `stage_new.dat` – Multall input file in new format. Use this in the following steps 

   - `stage_old.dat` – Multall input file in old format. Not needed 

   - – `blade_profiles.tec` – Blade shapes, can be opened in Tecplot 

   - `stagen.out` – Blade coordinates 

54 

- 3-stage axial turbine – blade profiles 

- Open Tecplot* and load `blade_profiles.tec` 

- Click on mapping style and show all data sets 

**==> picture [446 x 219] intentionally omitted <==**

Blade shape at the 1st (hub) section of the first blade row: 

55 

- 3-stage axial turbine – blade profiles 

- Select zone in all 3 data sets to examine a different blade 

**==> picture [377 x 183] intentionally omitted <==**

Blade section in row 4: 

**==> picture [297 x 254] intentionally omitted <==**

56 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- The _Stagen_ output file includes the stopping criteria (maximum number of iterations and the convergence limit) 

```
CFL,    DAMP,    MACHLIM,    F_PDOWN
0.400000 10.000000  2.000000  0.000000
IF_RESTART
0
```

```
NSTEPS_MAX, CONLIM
9000  0.001000
```

- Run _Multall_ 

```
>>Multall17.5.exe < stage_new.dat
```

- The program will not work without specifying the input file name! 

- Wait* until the computation converges or reaches the maximum number of iterations 

57 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- The run can be stopped with changing the value in the stopit file from 0 to 1.  This will save the results to `flow_out` and `grid_out.` 

- The calculation can be restarted form a previous run with `IF_RESTART=1` . For this the `flow_out` and `grid_out` file is needed 

```
CFL,    DAMP,    MACHLIM,    F_PDOWN
0.400000 10.000000  2.000000  0.000000
IF_RESTART
```

```
1
NSTEPS_MAX, CONLIM
9000  0.001000
```

- Starting from a previous run can make convergence much faster (in case of small modifications) or preliminary results can be saved by stopping and continuing the simulation 

58 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- Check the convergence of the results 

   - with _histage_ . 

**==> picture [247 x 309] intentionally omitted <==**

- Check if the mass 

flow was constant and the imbalance acceptably low* 

59 

**==> picture [125 x 540] intentionally omitted <==**

## 3 stage axial turbine - Multall 

- If efficiency and mass flow is lower than required... Geometry needs to be refined 

- Change the geometry ( `stagen.dat` ): 

   - Number of blades in row 

## – Blade profile specification 

```
0.0400    0.0400    0.3000    0.4500    0.0200    0.0100    2.0000     BLADE PROFILE SPECIFICATION
```

**==> picture [56 x 90] intentionally omitted <==**

TE thickness ratio Max. t/c Max. t/c location 

- What is the effect of these changes? 

60 

**==> picture [125 x 540] intentionally omitted <==**

## Postprocessing 

- Convert your results with: 

```
>>
convert-to-tecplot.exe
```

- This will make a _Tecplot_ input file from the and files `flow_out grid_out` 

- Select 2-3 blade passages. Selecting more blade passages can result in very large files (several gigabytes) 

- Open the `tecplot-input.dat` file in Tecplot 

61 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- Postprocess the results to check the geometry and mesh 

- Pressure distribution: 

**==> picture [283 x 253] intentionally omitted <==**

**==> picture [282 x 251] intentionally omitted <==**

62 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Blades 

- To show the blade surface: 

– Plot à Slices 

**==> picture [340 x 293] intentionally omitted <==**

- I-Planes 

- Show start/end 

63 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- Examine the flowfield in the root, meanline and tip section. 

- PlotàSlices. K-Planes 

- Mach number (hub, meanline, tip): 

**==> picture [233 x 207] intentionally omitted <==**

**==> picture [229 x 204] intentionally omitted <==**

64 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- In case of large Mach numbers change the blade shape (thickness and camber) 

- Mach number (M=0.5 isosurface): 

**==> picture [245 x 219] intentionally omitted <==**

- Check for supersonic flow. Modify blade shape (thickness and camber) in case of large Mach numbers 

65 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

## • Com arison of results: p 

||**Unit**|**Meanline**|**CFD**|
|---|---|---|---|
|Total-to-total efficiency|%|90|92.8|
|Mass flow rate|kg/m^3|25|25.1|
|Pressure ratio (t-t)|-||2.25|
|Power output|kW||2453|



- Check if target efficiency, required mass flow rate and pressure ratio was achieved 

66 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- How the calculated efficiency compares with the Smith chart? 

**==> picture [267 x 306] intentionally omitted <==**

67 

**==> picture [125 x 540] intentionally omitted <==**

3-stage axial turbine - Questions 

- Can you explain possible differences between preliminary and CFD results? 

- What is the effect of changing the degree of reaction? 

- What is the effect of changing the geometry (blade aspect ratio, solidity, etc)? 

- What is the effect of using untwisted blades instead of free vortex? 

- Run a calculation with a denser mesh (50×50 cells in the meridional section). Is there any difference in the results? 

68 

**==> picture [125 x 540] intentionally omitted <==**

# APPENDIX Cooling for first stage of HPT 

69 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

Cooling flows can be added at any point on the blade and endwall surfaces. The flow is added through a series of "patches" whose I,J,K boundaries are specified in the input data. If the "mixing plane" falls within a region where coolant is being added then two separate patches, one upstream and one downstream of the "mixing plane" must be used. The coolant mass flow, stagnation temperature, 

stagnation pressure, ejection Mach number and flow directions must be specified for each patch. Note that the exit relative Mach number of the coolant flow is specified and is not calculated from the local static and stagnation pressures. If it is required to model individual cooling holes then each patch may 

be one grid cell in size, but this requires a great deal of input data and it is more usual to specify a single patch to cover multiple cooling flows. The overall total-to-total efficiency is calculated and 

printed out, allowing for the potential work of all the cooling flows. However, the polytropic efficiencies, which are also printed out, relate the mass averaged inlet and outlet flow conditions and are not meaningful when cooling flows are added. 

Source: Denton: _J. Denton_ : MULTISTAGE TURBOMACHINERY FLOW CALCULATION PROGRAM MULTALL_OPEN 

70 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

## • Cooling options from the documentations: 

**==> picture [383 x 358] intentionally omitted <==**

71 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

## • Blade cooling: 

72 

**==> picture [720 x 540] intentionally omitted <==**

**----- Start of picture text -----**<br>
Cooling<br>•<br>Endwall cooling:<br>Blade passage: Blade surface:<br>flow<br>flow<br>73<br>**----- End of picture text -----**<br>


**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

- Effect of cooling patches on the temperature of 

   - blades and endwalls: 

Endwall cooling Blade cooling 

74 

## Blade cooling 

- Coordinates of the cooling patches 

KCBE, JCBE KCBE, JCBS Blade cooling patch KCBS, JCBE KCBS, JCBS 

75 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling – patch placement 

## • In `stage_new.dat` input file: 

```
******************************************************************************
***********STARTING THE INPUT FOR EACH BLADE ROW******************************
NOZZLE   ROW
```

```
NUMBER OF BLADES IN ROW
```

```
71
```

- `JM        JLE       JTE 141        26       126` 

- • Indices for cooling patch should be within these limits: 

𝐽𝐶𝐵𝑆≤𝐽𝐿𝐸, 𝐽𝐶𝐵𝐸≤𝐽𝑇𝐸 • WARNING – If the mesh density is changed, the position of the cooling patch will also change. 

76 

**==> picture [125 x 540] intentionally omitted <==**

## **Appendix** 

# **Multall tutorial by Denton** 

**77** 

## MULTALL – AN OPEN-SOURCE, CFD BASED, TURBOMACHINERY DESIGN SYSTEM 

ASME GT2017-63993 John Denton Retired from the Whittle Lab, Cambridge University, UK. The objective of this paper is to present a turbomachinery aerodynamic design system that is relatively simple to use and is freely available to anyone. 

**==> picture [152 x 282] intentionally omitted <==**

**==> picture [297 x 200] intentionally omitted <==**

**78** 

Turbomachinery design systems are usually the property of large companies and are very complex. 

The author has, over many years  developed a system based on his widely-used 3D CFD code MULTALL . The system is intended to be relatively simple and easy to use. The source codes are written in FORTRAN and are freely available to any user. 

It is hoped that this system will be of use to smaller companies and academics who do not have access to an “in-house” design system. 

**79** 

## : A turbomachinery design system generally consists of the following steps 

1. Specify overall parameters such as mass flow rate, mean diameter, rotational speed, inlet flow conditions, exit pressure. 

- 2 Perform a one-dimensional mean-line calculation to obtain the annulus shape and mid-span blade angles. 

3. Perform a 2D axisymmetric throughflow calculation in the inverse (design) mode to obtain the variation of flow angles along the span. 

4. Repeat the throughflow calculation in the analysis mode to predict the blade losses, machine efficiency and stream surface thickness distributions. 

5. Perform quasi-3D (Q3D) blade-to-blade calculations at several spanwise sections on each blade row to design the blade shapes. 

6. Perform relatively coarse grid, multistage, 3D, viscous calculations for the main flow path of the whole machine to optimise the blade stacking. 

7.   Perform more detailed 3D calculations to include the effects of leakage flows endwall bleeds and cavities and coolant flows. These will give the final prediction of machine overall performance. 

Each of these steps is likely to be repeated several times with returns to previous steps often being necessary. 

**80** 

The author has long maintained that, given a flexible geometry generator and a fast 3D solver, it is simpler and faster to omit steps 3 to 5,  and go straight from the mean line design to fairly coarse grid 3D calculations to . optimise the blade shapes and stacking 

This is the basis if the present design system. 

1. Specify overall parameters such as mass flow rate, mean diameter, rotational speed, inlet flow conditions, exit pressure. 

- 2 Perform a one-dimensional mean-line calculation to obtain the annulus shape and mid-span blade angles. 

3. Perform a 2D axisymmetric throughflow calculation in the inverse (design) mode to obtain the variation of flow angles along the span. 

4. Repeat the throughflow calculation in the analysis mode to predict the blade losses, machine efficiency and stream surface thickness distributions. 

5. Perform quasi-3D (Q3D) blade-to-blade calculations at several spanwise sections on each blade row to design the blade shapes. 

6. Perform relatively coarse grid, multistage, 3D, viscous calculations for the main flow path of the whole machine to optimise the **blade profiles** and the blade stacking. 

7.   Perform more detailed 3D calculations to include the effects of leakage flows endwall bleeds and cavities and coolant flows. These will give the final prediction of machine overall performance. 

**81** 

The quasi-3D calculations are anyhow not accurate unless twisted stream surfaces are used, as in Wu’s original suggestion. 

This is virtually never done ! 

The figure below shows the results of a Q3D  and a 3D calculation on a LP turbine blade where the mid-span section has been re-staggered by 5 deg. 

**==> picture [379 x 267] intentionally omitted <==**

**==> picture [180 x 189] intentionally omitted <==**

Static pressure contours on the blade with re-stagger, showing 3D relief. 

The Q3D calculation predicts the effect on loading to be about twice that of the 3D calculation. 

**82** 

MEANGEN Performs a 1D calculation to obtain the velocity triangles. Sets the annulus boundaries. Generates initial blade shapes and twists them for a free vortex design. Writes an input file for STAGEN 

**==> picture [321 x 92] intentionally omitted <==**

STAGEN Refines the blade shapes. Stacks them and combines them into stages. Writes an input file for MULTALL MULTALL Performs a 3D multistage calculation to predict the detailed flow pattern and overall performance. 

**83** 

## MEANGEN 

Takes input data either from the screen or from a file. 

The input is designed to be as minimal as possible so many parameters are set by default. These can be changed by editing the program. 

On the screen answer questions such as: 

Design a compressor or a turbine? Answer ‘C’  or ‘T’. Input the gas constant and specific heat ratio Input the desired mass flow rate. Input the rotational speed. 

etc. 

The screen input data is mirrored to a file and subsequent small changes to the design are most easily made by editing that file. 

The initial design can be run through STAGEN and MULTALL without any further changes if required, but it will usually need to be refined by STAGEN. 

**84** 

MEANGEN generates data for complete stages. Single blade rows can be generated by omitting the output for one of the blade rows. 

## The blading parameters can defined either: 

On a fixed radius and assuming repeating stage conditions. In which case only 3 parameters are needed to fix the velocity triangles. This makes it very easy to generate multiple repeating stages. 

## Or 

On an arbitrary stream surface with changes in radius and meridional velocity. In which case 4 parameters are needed to fix the velocity triangles, which can differ from stage to stage. 

The design stream surface can be either the hub, mid-span or tip. The variation of the blade angles along the span is obtained by assuming free vortex flow. 

**85** 

T                                      TURBO_TYP,"C" FOR A COMPRESSOR,"T" FOR A TURBINE AXI FLO_TYP FOR  AXIAL OR MIXED FLOW MACHINE 287.150       1.400               GAS PROPERTOES, RGAS, GAMMA 1.000     300.000               POIN,  TOIN 2                                  NUMBER OF STAGES IN THE MACHINE H CHOICE OF DESIGN POINT RADIUS, HUB, MID or TIP 3000.000 ROTATION SPEED, RPM 15.000 MASS FLOW RATE, FLOWIN. A INTYPE, TO CHOOSE THE METHOD OF DEFINING THE VELOCITY TRIANGLES 0.200     0.500     2.000    REACTION, FLOW COEFF., LOADING COEFF. A RADTYPE, TO CHOOSE THE DESIGN POINT RADIUS 0.400 THE DESIGN POINT RADIUS 

- 0.030       0.040                BLADE AXIAL CHORDS IN METRES. 

- 0.250       0.500                ROW GAP  AND STAGE GAP 

0.900 GUESS OF THE STAGE ISENTROPIC EFFICIENCY 

- 1.000       1.000                ESTIMATE OF THE DEVIATION ANGLES 

- -2.000      -2.000                FIRST AND SECOND ROW INCIDENCE ANGLES 

- 92.000    87.000                  QO ANGLES AT LE  AND TE OF ROW 1 

**==> picture [106 x 26] intentionally omitted <==**

This file, produced by answering questions on the screen. (Only the numbers and characters on the left are input) 

87.000    93.000                  QO ANGLES AT LE  AND TE OF ROW 2 

n DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE, ANSWER  "Y" or "N" y IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE VELOCITY TRIANGLES n DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE, ANSWER  "Y" or "N" Y                                      IS OUTPUT REQUESTED FOR ALL BLADE ROWS ? 

n STATOR No.  1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 

- 0.350       0.500                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  1 

- 0.350       0.475                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  2 

0.350       0.450                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  3 n ROTOR No.   1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 0.300       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  1 0.250       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  2 0.200       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  3 y STATOR No.  2 SET ANSTK= "Y" TO CHOOSE THE SAME BLADE SECTIONS AS THE LAST STAGE. y ROTOR No.  2 SET ANSTK= "Y" TO CHOOSE THE SAME BLADE SECTIONS AS THE LAST STAGE. 

Produces this Turbine 

**==> picture [324 x 186] intentionally omitted <==**

**86** 

## STAGEN 

Reads in a data file produced by MEANGEN. 

- Ø Allows the blade sections to be changed from the initial crude guess. 

- Ø Projects the blades onto quasi-stream surfaces. 

- Ø Stacks the blades. 

- Ø Generates the grid. 

- Ø Combines the blades into stages. 

- Ø Writes an input data file for MULTALL . 

As with MEANGEN many parameters are set by default and can be changed by editing the program. 

The blade profiles may be either: 

- Generated from a system of equations. 

- Generated from an input camber line and thickness distribution. 

- Read in from an existing profile. 

**87** 

## Blade thickness distributions from equations. 

**==> picture [214 x 265] intentionally omitted <==**

Root, mid and tip blade sections generated for an LP steam turbine last rotor. 

**88** 

## MULTALL 

## 3D multistage N-S solver developed over many years. Using on a finite volume time-marching method. 

## It can model most turbomachinery flow features, including: 

- Mixing plane model between blade rows. 

- Quasi-3D blade-to-blade calculations. 

- Axisymmetric throughflow calculations. 

- Three turbulence models. 

- Specified boundary layer transition point, or a simple transition model. 

- • Surface roughness effects. 

- Cooling flow addition through the blades or endwalls. 

- Bleed flows from the hub or casing. 

- Artificial compressibility for low Mach number and incompressible flows. 

- Pinched tip model for plain tip clearances. 

- Shroud leakage model for shrouded blades. 

- Temperature dependent gas properties. 

- Automatic matching of the grids at the mixing plane. 

- Ability to refine the grids within the code. 

- Automatic trailing edge cusp generation. 

- Modification of the inlet boundary conditions to simulate a repeating stage. 

- Ability to perform limited blade redesign within the 3D code. 

Most of these are briefly described in the paper, and in detail in the user manual, but there is no time to describe them here. 

**89** 

MULTALL uses a simple “H” grid, which is extremely simple to generate and is anyhow always necessary at mixing planes. However, use of an “H” mesh is much disapproved of by CFD specialists because of numerical errors on highly sheared cells. 

However, using cell corner storage of the variables, MULTALL works remarkably well on sheared grids, its speed and simplicity allow more cells to be used in highly sheared regions. 

Turbine leading edge stagnation point 

**==> picture [283 x 194] intentionally omitted <==**

Comparison with the exact solution on a 60deg staggered wedge. Inlet Mach number =1.6. 

**90** 

## MULTALL uses mixing planes between blade rows in relative motion. 

The mixing plane model has been refined over many years. There are two coincident pitchwise grid lines at the mixing plane. The flow quantities are extrapolated onto these lines and the flow between them is matched by a 1D timemarching procedure. 

**91** 

The mixing plane should allow pressure waves to intersect it without reflection and should mix out a potential flow without any loss. The flow downstream of it should have pitchwise uniform entropy and relative stagnation enthalpy. 

**==> picture [296 x 367] intentionally omitted <==**

**==> picture [320 x 313] intentionally omitted <==**

**92** 

**==> picture [336 x 243] intentionally omitted <==**

Entropy contours, the entropy is pitchwise uniform immediately downstream of the mixing plane. 

Entropy changes at a mixing plane. 

**==> picture [151 x 15] intentionally omitted <==**

The mass averaged entropy increases at the mixing plane as required for the mixing loss. 

Axial distance 

**93** 

## MULTALL can be run as a quasi-3D blade-to-blade solver by setting a single cell in the spanwise direction. 

**==> picture [233 x 138] intentionally omitted <==**

Any flow across the imaginary mid-cell line generates a pressure difference between the two end walls which keeps the flow on the stream surface. 

## Run times are of order 5-10 seconds per blade row. 

**==> picture [254 x 204] intentionally omitted <==**

**==> picture [234 x 200] intentionally omitted <==**

**==> picture [232 x 201] intentionally omitted <==**

45deg flare + 20% radius change. 

2D cascade. Constant stream surface thickness. 

Constant radius + 25% SS divergence. 

Same compressor blade row with different stream surfaces 

**94** 

## THROUGHFLOW CALCULATIONS 

The code can be run as an axisymmetric throughflow calculation by setting a single cell in the pitchwise direction. 

The full 3D geometry is input but far fewer grid points can be used. 

**==> picture [195 x 199] intentionally omitted <==**

As with the B-to-B method, any flow crossing the imaginary mid-passage line is made to increase the pressure on one blade surface and decrease it on the other. This gradually builds up a blade loading which keeps the flow on the mid-passage line. Deviation and incidence to the mid-passage line are added. 

Although the blade loading calculated in this way is only a rough approximation to the true loading its overall magnitude is compatible with the momentum change. 

**95** 

**==> picture [263 x 196] intentionally omitted <==**

LP Steam turbine. Streamlines. Full 3D . 

**==> picture [252 x 211] intentionally omitted <==**

LP steam turbine, blade surface pressure distributions from throughflow. 

## LP Steam turbine 

## Streamlines. Throughflow. 

**==> picture [328 x 232] intentionally omitted <==**

Comparison of throughflow and full 3D Mach numbers in LP steam turbine. 

**96** 

## Its advantages over conventional (streamline curvature) throughflow methods are: 

- It gives a crude estimate of blade loading. 

- It predicts the 3D effects of blade stacking. 

- The stability is not limited by the grid aspect ratio. 

- It predicts viscous losses on all solid surfaces via a very simple skin friction model. 

- • It predicts tip leakage flows and losses. 

- It predicts the growth of endwall boundary layers, but not the associated secondary flows. 

- It works with a specified exit pressure rather than a specified mass flow. 

- It works with choked blade rows, including predicting supersonic deviation. 

- It predicts normal shock waves but not oblique shocks. 

- It is very easy to change from throughflow to full 3D calculation – change 2 lines of data. 

## Its disadvantages are: 

- It does not work in the inverse (design) mode. 

- Run times are 5-10 seconds per blade row rather than a fraction of a second with streamline 

- curvature. 

- It requires a blade shape, although this can initially be a simple guess. 

- It does not give realistic pressure distributions for transonic compressors, but nor does any 

- throughflow method. 

- Users are not so familiar with the method. 

**97** 

## EXAMPLE OF USE OF THE DESIGN SYSTEM 

## Specify a large axial compressor with: 

Mass flow rate  50kg/s Stagnation pressure ratio = 2.0 Rotational speed = 5000 rpm Constant tip diameter = 1m Ambient inlet conditions 1bar, 300K . 

Assuming an isentropic efficiency = 90% , a 3 stage machine with a moderate stage loading coefficient = 0.36 should satisfy the requirement. 

o The inlet Mach number at the tip would be near sonic so to reduce this 15 of inlet swirl is chosen. This is gradually reduced so there is no swirl at exit. 

Run MEANGEN with specified inlet and outlet absolute flow angles (different for each stage), flow coefficient = 0.6, loading coefficient = 0.35. Design on the tip stream surface. 

Initially use a fairly coarse grid, 37x105x37, points per blade row.  No tip clearance or hub seal leakage. 

**98** 

For the initial runs make changes only in MEANGEN to get good flow on the design stream surface, no attempt to optimise the blade sections at other radii. 

M Produce an initial layout by running Meangen with default parameters and screen input. The solution has slightly low mass flow and pressure ratio. 

- M Increase the guess of deviation angles to increase the pressure ratio. Increase the blade thickness and blade numbers. Several runs to obtain flow and pressure ratio close to the 

- specified values. 

M The blades are mid-loaded. Move the point of maximum thickness and point of maximum camber forwards to obtain more fore-loaded blades. Reduce the trailing edge thickness. Several runs to obtain the required mass flow and pressure ratio. 

- M Move the point of maximum camber slightly further forwards. The blades now have good surface pressure distributions but there are high incidences on some sections. Adjust the average incidence angles for each row. Several runs. 

Total about 12  3D runs. Each run takes about 12 minutes on a single processor. 

**99** 

## Results from the FIRST run using MEANGEN alone. 

Meridional view with streamlines 

Mid-span Mach numbers 

**100** 

## Now make further changes by editing the STAGEN input file to refine the blade sections and adjust the incidences along the span 

S Change to a finer 55x140x55 point grid with tip gaps on all rotors, 5 cells in each tip gap. Adjust the incidence angles along the span. Rotor 3 is most highly loaded so increase its blade numbers. Several runs. 

- S Add hub shroud leakages on all stators. Adjust incidences. Several runs. 

- S Bow all stators, with pressure surfaces leaned towards the endwalls, to reduce endwall loadings. Re-adjust the incidences. The performance is now very close to specification with a predicted isentropic efficiency of 91.5% . 

- S To improve the stall margin add forwards sweep at all rotor tips by increasing the chord by 15% with a fixed trailing edge location. 

- S Further refine the blade incidences. Several runs. 

- S Run a characteristic from choke to stall. 

- S Run a very fine grid solution, 83x299x83 points per row, at the design point to check for any grid sensitivity. The mass flow and pressure ratio each changed by about 0.1% and the efficiency was 0.4% lower. 

Total about 17 3D runs, each taking about 30 minutes when starting from the previous solution. 

**101** 

## Uniformly loaded blades 

**==> picture [432 x 304] intentionally omitted <==**

Pressure ratio and efficiency slightly exceed the design targets 

**102** 

In total the design used about 30  3D runs, requiring about 12 hours CPU time on a single processor of a LINUX desktop (home) computer. 

However, more time than this is necessary for “thinking” about what changes to make next. 

Allowing for this, the design could be completed in about 3 person days. 

**103** 

## CONCLUSIONS 

The design system is relatively simple, easy to use and fast to run. 

However, as with any design process, it requires an experienced user to know what geometrical changes are needed to produce the required flow behaviour. Repeated use of the design system is a good way of acquiring such experience. MULTALL is a useful tool in its own right. It is simpler and faster than most CFD codes and some of the techniques used in it may be of use to other CFD developers. 

**==> picture [648 x 175] intentionally omitted <==**

**104** 

The FORTRAN source codes, user manuals and sample data sets can be downloaded as a folder named ‘multall-open’ from ‘dropbox’ using the following link. 

https://www.dropbox.com/sh/8i0jyxzjb57q4j4/AABD9GQ1MUFwUm5hMWFylucva?dl=0 

You do not need a ‘dropbox’ account to access this. 

A brief description of the system and a copy of the link is also available on the web site 

https://sites.google.com/view/multall-turbomachinery-design 

Any future developments to the programs or changes to the link will be announced on this web site. 

**105** 

## 10 stage compressor with overall pressure ratio 10:1 

**==> picture [371 x 306] intentionally omitted <==**

**==> picture [582 x 128] intentionally omitted <==**

**106** 

**==> picture [259 x 291] intentionally omitted <==**

Low Mach number flow around a cascade of cylinders. Maximum Mach number = 0.08. 

**==> picture [303 x 260] intentionally omitted <==**

**107** 

**==> picture [518 x 323] intentionally omitted <==**

Flow in a water pump. Contours of relative velocity. 

**108** 

**==> picture [125 x 540] intentionally omitted <==**

## **Appendix** 

**Basics on CFD for turbomachinery** Acknowledgements: A. Rubino - See also: http://www.cfd online.com/Wiki/Best_practice_guidelines_for_turbomachinery_CFD 

**109** 

## Hierarchy of CFD models 

**==> picture [720 x 330] intentionally omitted <==**

110 

## Multi-row simulation methods 

**==> picture [720 x 229] intentionally omitted <==**

**----- Start of picture text -----**<br>
Multall<br>**----- End of picture text -----**<br>


111 

## Throughflow simulations 

• Loss and deviation correlations. 

• Accuracy determined more by correlations than by numerical method. 

- Assumptions: – Circumferentiallyaveraged flow. 

- – Axisymmetric. 

**==> picture [347 x 185] intentionally omitted <==**

**==> picture [349 x 186] intentionally omitted <==**

112 

## Mixing-plane simulations 

**==> picture [364 x 154] intentionally omitted <==**

- Instantaneous mixing at mixing plane. 

• Non-uniform flow after mixing plane (conservation of mass, momentum and energy). 

**==> picture [309 x 233] intentionally omitted <==**

- Low computational cost. 

- Use for efficiency estimation. 

113 

## Frozen-rotor simulations 

- Rotor kept frozen with respect to stator. 

- Results depend on relative position rotor-stator. 

- If pitch ratio between rotorstator not integer, periodic BCs cannot be applied because of temporal lag. Use phase-lag periodic BCs. 

- Use to initialize unsteady computations with sliding mesh. 

- Used for interaction simulations between vaned and vaneless turbomachinery components (rotor-diffuser, impeller-volute, inlet-impeller). 

**==> picture [327 x 203] intentionally omitted <==**

**==> picture [243 x 203] intentionally omitted <==**

114 

## Sliding-mesh URANS simulations 

- Unsteady simulations. 

- Sliding motion between stationary and rotating mesh. 

- URANS as most accurate method for blade row calculations in industry. 

- High cost and memory requirements (not used for design optimization). 

- Initialize using a steady solution. 

**==> picture [291 x 185] intentionally omitted <==**

**==> picture [293 x 257] intentionally omitted <==**

115 

## Reduced Order Methods (ROM): Harmonic Balance 

- Unsteady simulations with a- priori known discrete set of frequencies (periodic phenomena). 

- Unsteady solution only for blade passing frequency harmonics. 

- Reduced computational cost, use for unsteady optimization. 

- • Possible numerical stability problems. 

- No initial transient as with URANS. 

- For >10 frequencies, computational cost can exceed URANS. 

- Stator-rotor interaction (known harmonics). 

**==> picture [174 x 223] intentionally omitted <==**

**==> picture [274 x 210] intentionally omitted <==**

116 

## Limitations of CFD for turbomachinery 

- Difficult prediction: 

   - Boundary layer transition. 

   - Turbulence. 

   - Endwall losses. 

   - Leakage flows. 

   - Leading-edge flow in compressors. 

   - Trailing-edge flow in turbines. 

- Modelling challenges: 

   - Geometrical details. 

   - Boundary conditions. 

   - Freestream turbulence. 

   - Endwall boundary layers. 

- Check convergence, physical sense, required information. 

117 



# --- END OF SOURCE: Multall Tutorial 2021 (including TecPlot).pdf ---



# ========================================================
# START OF SOURCE: Multall Tutorial 2023.pdf (Category: Multall Documentation)
# ========================================================

**==> picture [125 x 540] intentionally omitted <==**

## Multall 

## turbomachinery design tutorial 

Luis Matabuena Sedano (email) Matteo Pini 

Acknowledgements: John Denton, Pedro García Gozalez , Antonio Rubino, Peter Onodi, Pablo Garrido. 

1 

**==> picture [125 x 540] intentionally omitted <==**

## Overview 

- The **Multall-open** software package is an opensource Fortran code for turbomachinery design based on the 3D, multistage, Navier-Stokes solver Multall. 

- User manuals, documents on theoretical background are available on the BS package. 

- • This document includes information on the installation and use of the software, as well as some examples. 

- Additional notes are included below the slides, marked with an asterisk (*) 

- Most important take away: **READ THE DOCUMENTATION** 

2 

**==> picture [125 x 540] intentionally omitted <==**

## Multall Turbomachinery Design 

- The design software consists of 3 programs: 

   - Meangen – Meanline design 

   - Stagen – Geometry generation and meshing 

   - Multall – CFD 

- Source code, executables and manuals are available on Brightspace (AE4206 Turbomachinery – Content > Software). 

3 

MEANGEN Performs a 1D calculation to obtain the velocity triangles. Sets the annulus boundaries. Generates initial blade shapes and twists them in a prescribed way. Writes an input file for STAGEN. 

**==> picture [395 x 115] intentionally omitted <==**

STAGEN Generate the blade shapes. Stacks them and combines them into stages. Writes an input file for MULTALL 

MULTALL Performs a 3D multistage calculation to predict the detailed flow pattern and overall performance. 

**==> picture [87 x 35] intentionally omitted <==**

Source: Denton: _J. Denton_ : MULTALL – AN OPEN-SOURCE, CFD BASED, TURBOMACHINERY DESIGN SYSTEM 

**4** 

**==> picture [125 x 540] intentionally omitted <==**

## Data exchange with meanline design performed elsewhere 

**==> picture [522 x 413] intentionally omitted <==**

**----- Start of picture text -----**<br>
Multall-open software package<br>Basic blade geometry,<br>Meshing rules<br>Ψ,λ,γ<br>η → stagen.out – blade coord.<br>Your  own<br>meanline  design<br>(MATLAB, Excel,<br>Python,…)<br>**----- End of picture text -----**<br>


5 

**==> picture [125 x 540] intentionally omitted <==**

How to **install** Multall-open software package 

6 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on Windows-based machines 

1. Download the software as FORTRAN (.f) files. 2. Follow the steps of the MinGW-gfortran.pdf (available in this folder) to install the gfortran compiler on your command line. 

3. Open the meangen-17.4.f, stagen-18.1.f and multall-open-20.9.f files with a text editor, search for _dev/tty_ and comment the line that includes it by adding _**!**_ to the line. E.g.: `!OPEN(UNIT=5,  FILE= '/dev/tty’)` 4. Open the commall-open-20.9 file with a text editor and change the value marked in red in the first lines to around 30 (Windows presents a memory limitation, this number should not be higher than a certain limit)*: `PARAMETER(ID=30,JD=2500,KD=30,MAXKI=82 ,NRS=21,IG1=32,&JG1=1000,KG1=41)` 

7 

**==> picture [125 x 540] intentionally omitted <==**

- Install Multall-open software on Windows-based machines 

   1. Navigate to the folder in which you have the software (Multall\Source) using cd in the command line. 

   2. Type the following (in different lines): gfortran meangen-17.4.f -o meangen-17.4.exe gfortran stagen-18.1.f -o stagen-18.1.exe gfortran multall-open-20.9.f -o multall-open-20.9.exe 3. The executable files should appear in the folder in which the .f files are. 

   4. If there is no _intype_ file, create one and write _N_ on it. 

   5. Check the correct operation of the software using the test cases. 

8 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on macOS/Linux-based machines (1) 

- First of all, you’ll need to have installed Fortran on your machine. 

`o` For macOS: 

1. Install Xcode (available here https://itunes.apple.com/us/app/xcode/id497799835?mt=12) 

2. Install the Xcode command-line tools 

   - Open Terminal (Applications > Utilities > Terminal) and type **xcode-select --install** press Enter and follow the dialog boxes. 

3. Download and install Gfortran (from https://github.com/fxcoudert/gfortran-for-macOS/releases). Select the version based on your macOS release! 

`o` For Ubuntu: 

1. Open Terminal and type **sudo apt-get install gfortran** and press Enter. 

9 

**==> picture [125 x 540] intentionally omitted <==**

## Install Multall-open software on macOS/Linux-based machines (2) 

- Now, we need to compile the files ( _meangen-17.4.f_ , _multall-open-17.5.f_ and _stagen-17.2.f_ , located in the “ _Source code_ ” folder)  and create executables: 

   1. Open Terminal. 

   2. Navigate to the folder where the .f files that you want to compile are located by using the **cd** command followed by the path, and press Enter: 

**==> picture [303 x 26] intentionally omitted <==**

3. Once you are in the correct path, you can compile the .f file by using the following command: **gfortran -o meangen-17.4.exe meangen-17.4.f** 

**==> picture [410 x 14] intentionally omitted <==**

4. After a few seconds, a new file (.exe) will appear in the folder where the .f file was located. 

5. In order to execute this file, **you need to run it from the command window (Terminal)** . You can do this by dragging and dropping the .exe file to the Terminal window and pressing Enter or alternately by typing manually the path of the executable: 

- The steps followed can be repeated for the other files ( _multall-open-17.5.f_ and _stagen-17.2.f_ ), where the Folder and File names in steps 2 and 3 will need to be changed accordingly, 

10 

**==> picture [125 x 540] intentionally omitted <==**

How to **run** Multall-open software package 

11 

**==> picture [125 x 540] intentionally omitted <==**

## Meangen 

1. Run meangen-17.4.exe by double-clicking on the file. The following message should appear. 

**==> picture [300 x 196] intentionally omitted <==**

2. If answer S, the software will ask you to provide all the design parameters in the command line. 

3. If answer F, type the name of your own generated .in file, a text document with all the required design parameters (see next slide, recommended method). 

12 

**==> picture [125 x 540] intentionally omitted <==**

Meangen - Input example 

} type of machine („MIX” also for radial) 

*This also fixes your design radius: If you choose “T” the duty coefficients you introduce are implemented at the tip! 

You can also work with the real specific work 

Dispacement body (boundary layer) If n, properties can be specified For each blade row separately 

13 

**==> picture [125 x 540] intentionally omitted <==**

## Meangen - WARNING 

**==> picture [398 x 332] intentionally omitted <==**

14 

**==> picture [125 x 540] intentionally omitted <==**

## Stagen 

- Usage: double-click on stagen-18.1.exe 

   - Input: **stagen.dat** (output from Meangen). 

   - Output: `stage_new.dat` (and `stage_old.dat` ) 

   - The _intype_ file has to be set up to _N_ for the use of stage_new.dat. 

   - `Stagen.out` contains geometrical information 

15 

**==> picture [125 x 540] intentionally omitted <==**

## Stagen: Fine Tunning 

- Meangen assumes a lot of usual parameters for the design of the machine. They can be adjusted by recompiling the code or directly in **stagen.dat** 

## **Change the size of the mesh** 

Controls the spacing of the mesh (do not change) 

This tells Stagen.exe how to read the file, to define more sections Meangen must be modified 

**Change the size of the mesh in the meridional direction** (Cells before Blade, Cells on Blade, cells after blade) The following lines define the meridional mesh spacing (Do not change) 

**Number of Blades in the row** (This comes from Meangen applying the Zeweifel coefficient, do not change it randomly) 

Tip gaps and another features can be added! (Not required for the Project, check out documentation if curious) 

16 

**==> picture [125 x 540] intentionally omitted <==**

## Stagen: Fine Tunning 

## **Defines the section in the meridional direction** 

## **Line 40:** Caution, only change after reading documentation 

- XCUP: Number of upstream _local chord_ length that the computational domain is extended. 

- XCDWN: The same, but downstream of the Blade row 

- BETUP, BETDWN: Upstream and downstream angles of the grid, the same as the blade. Do **not** change 

## **Line 42:** 

- Must match the number of points in the following two lines 

## **Line 43-44:** 

- Define the Surface where the Blade section is generated (Next slide) 

## **Line 45:** Do NOT change 

- LE and TE coordinates, must be points in the previous list 

## **Line 46:** Check out documentation 

- Multall suports more complex Blade stacking! (Not required for the project) 

17 

**==> picture [125 x 540] intentionally omitted <==**

## Stagen: Fine Tunning 

## **Defines the section in the meridional direction** 

## **Line 43:** x coordinate 

- The first and last points must be outside the computational domain. 

- • Multall generates This taking into account the Blade LE and TE Q angles specified. 

- Multall generates: 

   - 2 Points before the first row LE 

   - 4 

   - • First row LE • First Row TE 𝑟 𝑅𝑖𝐿4,𝑖 𝑥 𝑥= ෍ 

   - • Mixing plane position 𝑖=𝑖 4 

   - • Second Row LE 𝑥−𝑋 𝑗 

   - 𝐿 

   - • Second Row TE 4,𝑖 = ෑ 𝑋𝑖 −𝑋𝑗 • 2 Points after the second row 𝑗=1 𝑗≠𝑖 

## **Line 43:** r coordinate 

- Multall generates the gas path taking into account the (expected) changes in fluid properties as well as the (user supplied) blockage factor. 

- Points bwtween the control ones are obtained by using 3 order polynomical interpolation. 

- Multall guessed values are good and massflow should be matched by changing ሶ𝑚 and blockage in meangen.in, this is an (optional) opportunity to change the shape, **not** intentended as the main workflow line 

18 

**==> picture [125 x 540] intentionally omitted <==**

## Multall 

Settings related to turbulence model, fluid model, CFL number and other simulation parameters may be changed by modifying stagen_new.dat 

- Cp and gamma based on flow properties. 

- CFL number for CFD simulations. 

- NSTEPS_MAX determines the maximum number of iterations. 

- CONLIM determines the convergence of the simulation (default value of 0.001%). 

19 

**==> picture [125 x 540] intentionally omitted <==**

## Multall-Convergence 

- : 

- Maximum iteration, convergence limit in `stage_new.dat` 

**==> picture [345 x 55] intentionally omitted <==**

**%, This is equivalent to 0.00001 in CFX** 

- This file also contains KM and IM, DO NOT change them here, the mesh has been already generated. 

- To stop a running simulation prematurely (and still save the results): 

   - Open „stopit” file 

   - Change 0 to 1 

- To generate intermediate results (They do not have to represent physical data, it is a numerical intermediate state): 

**==> picture [570 x 42] intentionally omitted <==**

20 

**==> picture [125 x 540] intentionally omitted <==**

## Multall - run 

- To run the solver in cmd and save the results to file: 

```
>> multall-open-20.9.exe <
```

`stage_new.dat > results.txt` (This is one line!) 

- It Will writte in results.txt while running: Useful to 

   - control the convergence of your run. 

- Once it is finish, results.txt contains data as efficiency and mass flow of the machine 

21 

**==> picture [125 x 540] intentionally omitted <==**

## Plotting programs 

- They have been lost to time. You are very free to check out the documentation, find them, and link them back to the executable. 

- Transition towards ParaView: A lot of plotting can be done in PostPy (Thge most interesting metrics. If something more is required contact email, or implement it yourself!) 

22 

**==> picture [125 x 540] intentionally omitted <==**

How to **post-process** Multall-open software package 

23 

**==> picture [125 x 540] intentionally omitted <==**

## Postprocessing – PostPy/ParaView 

- Refer to PostPy documentation 

- **ParaView/Tecplot** compatible files 

24 

**==> picture [125 x 540] intentionally omitted <==**

## Design **Examples** 

(Credit to the correspondant author) 

25 

**==> picture [125 x 540] intentionally omitted <==**

# **Design example 1** Design of first stage of HPC for NASA E3 engine 

**26** 

## Design specifications 

|**Specification**|**Value**|
|---|---|
|Inlet total pressure (Pa)|276000|
|Inlet total temperature (K)|340|
|Overall pressure ratio|14|
|Mass flow rate (kg/s)|88.23|
|Rotational speed (rpm)|13177|
|1st stage inlet corrected tip speed (m/s)|379.5|
|IGV|No|



**==> picture [87 x 35] intentionally omitted <==**

27 

## Steps 

## **The first step is to modify the inputs in the meangen.in file:** 

1. Write the parameters that are already known from the design specifications (e.g. inlet total temperature and pressure). 

2. Select the number of stages considering constant work per stage. _Hint: Consider reference values for maximum stage pressure ratio (around 1.6) and maximum flow deflection to avoid separation._ 

3. Select load coefficient, flow coefficient and degree of reaction based on design criteria. 

4. Compute design point radius based on continuity equation. 5. Select axial chords based on selected solidity. 

6. Provide estimates for row and stage gaps, and of blockage factors due to boundary layer. 

7. Provide an estimated of the stage isentropic efficiency based on empirical data (e.g. Smith chart) or calculations (e.g. loss models). 

8. Provide estimates of deviation and incidence angles based on models (e.g. Traupel, Greitzer, Ainley & Mathieson…). 

9. Provide taper if desired (QO angles). 

10. First estimate of blade max thickness and location (can be changed in Stagen). 

**==> picture [87 x 35] intentionally omitted <==**

28 

Steps 

**==> picture [720 x 389] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

29 

## Steps 

**Run meangen-17.4.exe, selecting input from file (write F in cmd). Outputs:** 

- meangen.out: slight modifications from meangen.in (e.g. number of decimals), check if the values are roughly the same). 

- stagen.dat: inputs for Stagen. 

**Modify stagen.dat (make changes on local blade profile characteristics based on fluid-dynamic understanding of turbomachinery behaviour, loss models, and the indications provided in the tutorial by Denton in the appendix of this ppt):** 

1. Change IM, KM to a value lower than the limit defined in commall. 

2. Change NPOINTS to perform grid convergence study (the higher the number, the higher the accuracy of CFD results, but the higher the computational time). _See the tutorial by Denton in the appendix for more information._ 

3. Number of blades can also be modified if the solidity estimate does not lead to satisfactory results. 

4. Change detailed profile characteristics (see next slides). 

**==> picture [87 x 35] intentionally omitted <==**

30 

## Steps 

**==> picture [715 x 374] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

31 

## Steps 

**==> picture [682 x 387] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

32 

## Steps 

**==> picture [661 x 368] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

33 

## Steps 

**==> picture [666 x 373] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

34 

## Steps 

**==> picture [663 x 371] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

35 

## Steps 

**==> picture [717 x 372] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

36 

## Steps 

**==> picture [694 x 371] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

37 

## Steps 

## **Run stagen-18.1.exe. Write the name of your file in the cmd. Outputs:** 

- stagen.out: blade profile coordinates. 

- blade_profiles.tec: blade profiles in format readable by Tecplot. 

- stage_new.dat: inputs for Multall. 

- stage_old.dat: inputs for old version of Multall. 

## **Change parameters of CFD simulation if necessary:** 

1. Cp and gamma have been defined in meangen.in, check if correct. 

2. CFL number to ensure convergence of CFD simulations. 

3. Maximum Mach number is defined as MACHLIM. 

4. Convergence parameters as defined as the maximum number of steps (NSTEPS_MAX) and the convergence parameter (CONLIM), which are given standard values of 9000 and 0.1%. 

5. IM and KM can again be changed in this file. 

**==> picture [87 x 35] intentionally omitted <==**

38 

## Steps 

**Run Multall by the following command in cmd (after cd-ing to the folder):** `multall-open-20.9.exe < stage_new.dat > results.txt` 

## **Wait until the simulation has converged (can take several minutes).** 

**. Check convergence with** _**histage**_ 

## **For postprocessing:** 

1. Convert results using _convert-to-tecplot.exe_ using 1-2 blade passages _._ This will make a Tecplot input file from the flow_out and grid_out files. 

2. Open the tecplot-input.dat file in Tecplot. 

3. Obtain the distribution of different properties in Details, behind the Contour box. A certain flow slice can be selected. 

4. Equations can be defined to obtain the desired parameters and compute losses. 

**==> picture [87 x 35] intentionally omitted <==**

39 

## Steps 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [385 x 540] intentionally omitted <==**

40 

## Steps 

**==> picture [342 x 350] intentionally omitted <==**

## **Mach number distribution** 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [374 x 428] intentionally omitted <==**

**Total pressure distribution along radius (shockwave formation seen close to tip)** 

41 

## Steps 

## • Comparison of results: 

|**Parameter**|**Unit**|**Meanline**|**CFD**|
|---|---|---|---|
|**Total-to-total efficiency**|%|91.2|88.8|
|**Mass flow rate**|kg/m^3|88.23|88.13|
|**Pressure ratio**|-|1.6|1.59|



• Check if target efficiency, required mass flow rate and pressure ratio are achieved. 

**==> picture [87 x 35] intentionally omitted <==**

42 

# **Design example 2 3-stage axial turbine** 

**==> picture [87 x 35] intentionally omitted <==**

**43** 

**==> picture [125 x 540] intentionally omitted <==**

## Example: 3-stage axial turbine 

- This example shows the steps from the end of a preliminary design until CFD calculation and postprocessing and evaluating the results 

- The following preliminary design results are given: 

||**Unit**|**Value**|
|---|---|---|
|Inlet total pressure|bar|2|
|Inlet total temperature|K|500|
|Blade twist||Free vortex|
|Hub radius (const.)|m|0.4|
|Target total-to-total<br>efficiency|%|90|
|Mass flow rate|kg/m^3|25|
|Rotation speed|RPM|3000|
|Degree of reaction|-|0.25|
|Flow coefficient|-|0.5|
|Work coefficient|-|2|



• Same flow coefficient, load coefficient and degree of reaction is used for all stages. 

44 

**==> picture [125 x 540] intentionally omitted <==**

Example: 3-stage axial turbine 

- Blade chords are selected based on the calculated blade span and by selecting a proper aspect ratio. 

- Row gaps are selected 

- Incidence and deviation angles, blade thickness ratios and blockage factors are estimated 

- From the preliminary calculations and design choices the Meangen input file* is constructed → 

45 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Meangen Meangen input file (name the file `meangen.in` ):* 

|`T`|`TURBO_TYP,"C" FOR A COMPRESSOR,"T"FOR A TURBINE`|
|---|---|
|`AXI`|`FLO_TYP FORAXIAL OR MIXED FLOW MACHINE`|
|`287.500     1.400     GAS PROPERTOES, RGAS, GAMMA`||
|`2.000   500.000POIN,  TOIN`||
|`3`|`NUMBER OF STAGES IN THE MACHINE`|
|`H`|`CHOICE OF DESIGN POINT RADIUS,HUB, MID or TIP`|
|`3000.000`|`ROTATION SPEED, RPM`|
|`25.000`|`MASS FLOW RATE, FLOWIN.`|
|`A`|`INTYPE, TO CHOOSE THE METHOD OF DEFINING THE VELOCITY TRIANGLES`|
|`0.250  0.500  2.000    REACTION, FLOW COEFF., LOADING COEFF.`||
|`A`|`RADTYPE, TO CHOOSE THE DESIGN POINT RADIUS`|
|`0.400`|`THE DESIGN POINT RADIUS`|
|`0.050`|`0.040 BLADE AXIAL CHORDS IN METRES.`|
|`0.250`|`0.500 ROW GAP  AND STAGE GAP (fractions)`|
|`0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE`||
|`0.900`|`GUESS OF THE STAGE ISENTROPIC EFFICIENCY`|
|`1.000   1.000`|`ESTIMATE OF THE FIRST AND SECOND ROW DEVIATION ANGLES`|
|`-2.000  -2.000`|`FIRST AND SECOND ROW INCIDENCE ANGLES`|
|`1.00000`|`BLADE TWIST OPTION, FRAC_TWIST (1 is free vortex, 0 is without twist)`|
|`n`|`BLADE ROTATION OPTION , Y or N`|
|`92.000  88.000`|`QO ANGLES AT LE  AND TE OF ROW 1`|
|`88.000  92.000`|`QO ANGLES AT LE  AND TE OF ROW 2`|
|`n`|`DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"`|
|`y`|`IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE INPUT TYPE AND VELOCITY TRIANGLES, SET = "C" TO CHANG E`|
|`INPUT TYPE.`||
|`0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE`||
|`n`|`DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"`|
|`y`|`IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE INPUT TYPE AND VELOCITY TRIANGLES, SET = "C" TO CHANG E`|
|`INPUT TYPE.`||



- `0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE` 

- `n                        DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N" Y                        IS OUTPUT REQUESTED FOR ALL BLADE ROWS ? N    STATOR No.  1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE` 

- `0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  1` 

- `0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  2 0.3000  0.4500         MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  3` 

- `Y    ROTOR No.   1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE Y    STATOR No.  2 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE Y    ROTOR No.   2 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE Y    STATOR No.  3 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE Y    ROTOR No.   3 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE` 

46 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

• Before starting the calculations make sure to have all of the following files in the same folder: 

**==> picture [538 x 204] intentionally omitted <==**

47 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

- Run _Meangen_ in the command line with the input file ( `meangen.in` ). `>>Meangen17.4.1.exe` 

- Press „F” to input the data* from file 

- This generates the input file for Stagen (next slide) 

48 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

## • _Meangen_ ouputs 3 new files: 

   - `meandesign.out` – row geometry & thermodynamics 

   - – `meangen.out` – echo of the Meangen input file 

   - `stagen.dat` – Stagen input file 

- meandesign.out includes thermodynamic properties, geometry and the data for velocity triangles for each blade row: 

```
STAGE No, ROW No, No. BLADES 1 1 33
STAGE No, ROW No, No. BLADES 1 2 71
```

```
*****************************************************
CONDITIONS FOR THE FIRST BLADE ROW OF THE STAGE.
THIS IS A TURBINE STATOR
```

```
*****************************************************
FIRST BLADE INLET AND EXIT ANGLES  -26.565073
74.054665
```

```
FIRST BLADE AXIAL VELOCITY      62.8318
FIRST BLADE INLET MACH NUMBER   0.15697631
FIRST BLADE EXIT MACH NUMBER    0.52361447
FIRST BLADE EXIT DENSITY        1.201726
FIRST BLADE EXIT PRESSURE       1.6376798
FIRST BLADE INLET STAGN PRESS   2.0000002
FIRST BLADE EXIT STAGN PRESS    1.9741219
FIRST BLADE REL INLET STAG PRES 2.0000002
FIRST BLADE EXIT TEMPERATURE    474.00806
FIRST BLADE EXIT STAGN TEMP     500.
FIRST BLADE TIP RADIUS =        0.5021015
FIRST BLADE INLET SPAN =        0.107626915
FIRST BLADE AXIAL CHORD=        0.05
```

```
FIRST BLADE ASPECT RATIO =      2.1525383
```

```
…
```

49 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Meshing 

## • In `stagen.dat` the mesh size can be changed*: 

```
287.5000      1.4000 GAS CONSTANT, GAMMA
37        37     IM, KM
1.2500     20.0000  FPRAT,  FPMAX
1.2500     20.0000  FRRAT,  FRMAX
0               IFDEFAULTS
6         3     NOWS, N SECTIONS
1.000               SCALING FACTOR
```

## • Run Stagen. This generates the mesh `>>Stagen17.2.2.exe` 

- Answer with yes (y) for the question about the input file name 

- _Stagen_ will produce the following files: 

   - `stage_new.dat` – Multall input file in new format. Use this in the following steps 

   - `stage_old.dat` – Multall input file in old format. Not needed 

   - – `blade_profiles.tec` – Blade shapes, can be opened in Tecplot 

   - `stagen.out` – Blade coordinates 

50 

- 3-stage axial turbine – blade profiles 

- Open Tecplot* and load `blade_profiles.tec` 

- Click on mapping style and show all data sets 

**==> picture [446 x 219] intentionally omitted <==**

Blade shape at the 1st (hub) section of the first blade row: 

51 

## 3-stage axial turbine – blade profiles 

- Select zone in all 3 data sets to examine 

## a different blade 

**==> picture [375 x 182] intentionally omitted <==**

## Blade section in row 4: 

**==> picture [296 x 254] intentionally omitted <==**

52 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- The _Stagen_ output file includes the stopping criteria (maximum number of iterations and the convergence limit) 

```
CFL,    DAMP,    MACHLIM,    F_PDOWN
0.400000 10.000000  2.000000  0.000000
IF_RESTART
0
NSTEPS_MAX, CONLIM
9000  0.001000
```

## • Run _Multall_ 

```
>>Multall17.5.exe < stage_new.dat
```

- The program will not work without specifying the input file name! 

- Wait* until the computation converges or reaches the maximum number of iterations 

53 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- The run can be stopped with changing the value in the stopit file from 0 to 1.  This will save the results to `flow_out` and `grid_out.` 

- The calculation can be restarted form a previous run with `IF_RESTART=1` . For this the `flow_out` and `grid_out` file is needed 

```
CFL,    DAMP,    MACHLIM,    F_PDOWN
0.400000 10.000000  2.000000  0.000000
IF_RESTART
```

```
1
NSTEPS_MAX, CONLIM
9000  0.001000
```

- Starting from a previous run can make convergence much faster (in case of small modifications) or preliminary results can be saved by stopping and continuing the simulation 

54 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - CFD 

- Check the convergence of the results 

   - with _histage_ . 

**==> picture [246 x 308] intentionally omitted <==**

- Check if the mass 

flow was constant and the imbalance acceptably low* 

55 

**==> picture [125 x 540] intentionally omitted <==**

## 3 stage axial turbine - Multall 

- If efficiency and mass flow is lower than required... Geometry needs to be refined 

- Change the geometry ( `stagen.dat` ): 

   - Number of blades in row 

## – Blade profile specification 

```
0.0400    0.0400    0.3000    0.4500    0.0200    0.0100    2.0000     BLADE PROFILE SPECIFICATION
```

**==> picture [56 x 89] intentionally omitted <==**

TE thickness ratio Max. t/c Max. t/c location 

- What is the effect of these changes? 

56 

**==> picture [125 x 540] intentionally omitted <==**

## Postprocessing 

- Convert your results with: 

```
>>
convert-to-tecplot.exe
```

- This will make a _Tecplot_ input file from the and files `flow_out grid_out` 

- Select 2-3 blade passages. Selecting more blade passages can result in very large files (several gigabytes) 

- Open the `tecplot-input.dat` file in Tecplot 

57 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- Postprocess the results to check the geometry and mesh 

- Pressure distribution: 

**==> picture [283 x 252] intentionally omitted <==**

**==> picture [281 x 250] intentionally omitted <==**

58 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Blades 

- To show the blade surface: 

– Plot → Slices 

**==> picture [340 x 293] intentionally omitted <==**

– I-Planes 

– Show start/end 

59 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- Examine the flowfield in the root, meanline and tip section. 

- Plot→Slices. K-Planes 

- Mach number (hub, meanline, tip): 

**==> picture [229 x 204] intentionally omitted <==**

**==> picture [232 x 207] intentionally omitted <==**

60 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- In case of large Mach numbers change the blade shape (thickness and camber) 

- Mach number (M=0.5 isosurface): 

**==> picture [244 x 219] intentionally omitted <==**

- Check for supersonic flow. Modify blade shape (thickness and camber) in case of large Mach numbers 

61 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine 

## • Com arison of results: p 

||**Unit**|**Meanline**|**CFD**|
|---|---|---|---|
|Total-to-total efficiency|%|90|92.8|
|Mass flow rate|kg/m^3|25|25.1|
|Pressure ratio (t-t)|-||2.25|
|Power output|kW||2453|



- Check if target efficiency, required mass flow rate and pressure ratio was achieved 

62 

**==> picture [125 x 540] intentionally omitted <==**

## 3-stage axial turbine - Multall 

- How the calculated efficiency compares with the Smith chart? 

**==> picture [267 x 306] intentionally omitted <==**

63 

**==> picture [125 x 540] intentionally omitted <==**

3-stage axial turbine - Questions 

- Can you explain possible differences between preliminary and CFD results? 

- What is the effect of changing the degree of reaction? 

- What is the effect of changing the geometry (blade aspect ratio, solidity, etc)? 

- What is the effect of using untwisted blades instead of free vortex? 

- Run a calculation with a denser mesh (50×50 cells in the meridional section). Is there any difference in the results? 

64 

**==> picture [125 x 540] intentionally omitted <==**

**APPENDIX** Cooling for first stage of HPT 

65 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

Cooling flows can be added at any point on the blade and endwall surfaces. The flow is added through a series of "patches" whose I,J,K boundaries are specified in the input data. If the "mixing plane" falls within a region where coolant is being added then two separate patches, one upstream and one downstream of the "mixing plane" must be used. The coolant mass flow, stagnation temperature, 

stagnation pressure, ejection Mach number and flow directions must be specified for each patch. Note that the exit relative Mach number of the coolant flow is specified and is not calculated from the local static and stagnation pressures. If it is required to model individual cooling holes then each patch may 

be one grid cell in size, but this requires a great deal of input data and it is more usual to specify a single patch to cover multiple cooling flows. The overall total-to-total efficiency is calculated and 

printed out, allowing for the potential work of all the cooling flows. However, the polytropic efficiencies, which are also printed out, relate the mass averaged inlet and outlet flow conditions and are not meaningful when cooling flows are added. 

Source: Denton: _J. Denton_ : MULTISTAGE TURBOMACHINERY FLOW CALCULATION PROGRAM MULTALL_OPEN 

66 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

## • Cooling options from the documentations: 

**==> picture [383 x 358] intentionally omitted <==**

67 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

## • Blade cooling: 

68 

**==> picture [720 x 540] intentionally omitted <==**

**----- Start of picture text -----**<br>
Cooling<br>•<br>Endwall cooling:<br>Blade passage: Blade surface:<br>flow<br>flow<br>69<br>**----- End of picture text -----**<br>


**==> picture [125 x 540] intentionally omitted <==**

## Cooling 

- Effect of cooling patches on the temperature of 

   - blades and endwalls: 

Endwall cooling Blade cooling 

70 

## Blade cooling 

- Coordinates of the cooling patches 

Blade cooling patch KCBS, JCBE KCBS, JCBS 

KCBE, JCBE KCBE, JCBS 

**==> picture [87 x 35] intentionally omitted <==**

71 

**==> picture [125 x 540] intentionally omitted <==**

## Cooling – patch placement 

## • In `stage_new.dat` input file: 

```
******************************************************************************
***********STARTING THE INPUT FOR EACH BLADE ROW******************************
NOZZLE   ROW
```

```
NUMBER OF BLADES IN ROW
71
```

```
JM        JLE       JTE
```

```
141        26       126
```

- Indices for cooling patch should be within these limits: 

- 𝐽𝐶𝐵𝑆≤𝐽𝐿𝐸, 𝐽𝐶𝐵𝐸≤𝐽𝑇𝐸 

- • WARNING – If the mesh density is changed, the position of the cooling patch will also change. 

72 

**==> picture [125 x 540] intentionally omitted <==**

## **Appendix** 

# **Multall tutorial by Denton** 

**73** 

## MULTALL – AN OPEN-SOURCE, CFD BASED, TURBOMACHINERY DESIGN SYSTEM 

ASME GT2017-63993 John Denton Retired from the Whittle Lab, Cambridge University, UK. The objective of this paper is to present a turbomachinery aerodynamic design system that is relatively simple to use and is freely available to anyone. 

**==> picture [152 x 282] intentionally omitted <==**

**==> picture [297 x 200] intentionally omitted <==**

**74** 

Turbomachinery design systems are usually the property of large companies and are very complex. 

The author has, over many years  developed a system based on his widely-used 3D CFD code MULTALL . The system is intended to be relatively simple and easy to use. The source codes are written in FORTRAN and are freely available to any user. 

It is hoped that this system will be of use to smaller companies and academics who do not have access to an “in-house” design system. 

**==> picture [87 x 35] intentionally omitted <==**

**75** 

## : A turbomachinery design system generally consists of the following steps 

1. Specify overall parameters such as mass flow rate, mean diameter, rotational speed, inlet flow conditions, exit pressure. 

- 2 Perform a one-dimensional mean-line calculation to obtain the annulus shape and mid-span blade angles. 

3. Perform a 2D axisymmetric throughflow calculation in the inverse (design) mode to obtain the variation of flow angles along the span. 

4. Repeat the throughflow calculation in the analysis mode to predict the blade losses, machine efficiency and stream surface thickness distributions. 

5. Perform quasi-3D (Q3D) blade-to-blade calculations at several spanwise sections on each blade row to design the blade shapes. 

6. Perform relatively coarse grid, multistage, 3D, viscous calculations for the main flow path of the whole machine to optimise the blade stacking. 

7.   Perform more detailed 3D calculations to include the effects of leakage flows endwall bleeds and cavities and coolant flows. These will give the final prediction of machine overall performance. 

Each of these steps is likely to be repeated several times with returns to previous steps often being necessary. 

**76** 

The author has long maintained that, given a flexible geometry generator and a fast 3D solver, it is simpler and faster to omit steps 3 to 5,  and go straight from the mean line design to fairly coarse grid 3D calculations to . optimise the blade shapes and stacking 

## This is the basis if the present design system. 

1. Specify overall parameters such as mass flow rate, mean diameter, rotational speed, inlet flow conditions, exit pressure. 

- 2 Perform a one-dimensional mean-line calculation to obtain the annulus shape and mid-span blade angles. 

3. Perform a 2D axisymmetric throughflow calculation in the inverse (design) mode to obtain the variation of flow angles along the span. 

4. Repeat the throughflow calculation in the analysis mode to predict the blade losses, machine efficiency and stream surface thickness distributions. 

5. Perform quasi-3D (Q3D) blade-to-blade calculations at several spanwise sections on each blade row to design the blade shapes. 

6. Perform relatively coarse grid, multistage, 3D, viscous calculations for the main flow path of the whole machine to optimise the **blade profiles** and the blade stacking. 

7.   Perform more detailed 3D calculations to include the effects of leakage flows endwall bleeds and cavities and coolant flows. These will give the final prediction of machine overall performance. 

**==> picture [87 x 35] intentionally omitted <==**

**77** 

The quasi-3D calculations are anyhow not accurate unless twisted stream surfaces are used, as in Wu’s original suggestion. 

This is virtually never done ! 

The figure below shows the results of a Q3D  and a 3D calculation on a LP turbine blade where the mid-span section has been re-staggered by 5 deg. 

**==> picture [379 x 267] intentionally omitted <==**

**==> picture [180 x 189] intentionally omitted <==**

Static pressure contours on the blade with re-stagger, showing 3D relief. 

The Q3D calculation predicts the effect on loading to be about twice that of the 3D calculation. 

**78** 

MEANGEN Performs a 1D calculation to obtain the velocity triangles. Sets the annulus boundaries. Generates initial blade shapes and twists them for a free vortex design. Writes an input file for STAGEN 

**==> picture [395 x 115] intentionally omitted <==**

STAGEN Refines the blade shapes. Stacks them and combines them into stages. Writes an input file for MULTALL 

**==> picture [87 x 35] intentionally omitted <==**

MULTALL Performs a 3D multistage calculation to predict the detailed flow pattern and overall performance. 

**79** 

## MEANGEN 

Takes input data either from the screen or from a file. 

The input is designed to be as minimal as possible so many parameters are set by default. These can be changed by editing the program. 

On the screen answer questions such as: 

Design a compressor or a turbine? Answer ‘C’  or ‘T’. Input the gas constant and specific heat ratio Input the desired mass flow rate. Input the rotational speed. 

etc. 

The screen input data is mirrored to a file and subsequent small changes to the design are most easily made by editing that file. 

The initial design can be run through STAGEN and MULTALL without any further changes if required, but it will usually need to be refined by STAGEN. 

**==> picture [87 x 35] intentionally omitted <==**

**80** 

MEANGEN generates data for complete stages. Single blade rows can be generated by omitting the output for one of the blade rows. 

## The blading parameters can defined either: 

On a fixed radius and assuming repeating stage conditions. In which case only 3 parameters are needed to fix the velocity triangles. This makes it very easy to generate multiple repeating stages. 

## Or 

On an arbitrary stream surface with changes in radius and meridional velocity. In which case 4 parameters are needed to fix the velocity triangles, which can differ from stage to stage. 

The design stream surface can be either the hub, mid-span or tip. The variation of the blade angles along the span is obtained by assuming free vortex flow. 

**==> picture [87 x 35] intentionally omitted <==**

**81** 

T                                      TURBO_TYP,"C" FOR A COMPRESSOR,"T" FOR A TURBINE AXI FLO_TYP FOR  AXIAL OR MIXED FLOW MACHINE 287.150       1.400               GAS PROPERTOES, RGAS, GAMMA 1.000     300.000               POIN,  TOIN 2                                  NUMBER OF STAGES IN THE MACHINE H CHOICE OF DESIGN POINT RADIUS, HUB, MID or TIP 3000.000 ROTATION SPEED, RPM 15.000 MASS FLOW RATE, FLOWIN. A INTYPE, TO CHOOSE THE METHOD OF DEFINING THE VELOCITY TRIANGLES 0.200     0.500     2.000    REACTION, FLOW COEFF., LOADING COEFF. A RADTYPE, TO CHOOSE THE DESIGN POINT RADIUS 0.400 THE DESIGN POINT RADIUS 0.030       0.040                BLADE AXIAL CHORDS IN METRES. 0.250       0.500                ROW GAP  AND STAGE GAP 0.900 GUESS OF THE STAGE ISENTROPIC EFFICIENCY 1.000       1.000                ESTIMATE OF THE DEVIATION ANGLES -2.000      -2.000                FIRST AND SECOND ROW INCIDENCE ANGLES 92.000    87.000                  QO ANGLES AT LE  AND TE OF ROW 1 87.000    93.000                  QO ANGLES AT LE  AND TE OF ROW 2 n DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE, ANSWER  "Y" or "N" y IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE VELOCITY TRIANGLES n DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE, ANSWER  "Y" or "N" Y                                      IS OUTPUT REQUESTED FOR ALL BLADE ROWS ? 

n STATOR No.  1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 0.350       0.500                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  1 0.350       0.475                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  2 0.350       0.450                MAX THICKNESS AND ITS LOCATION FOR STATOR  1 SECTION No.  3 n ROTOR No.   1 SET ANSTK = "Y" TO USE THE SAME  BLADE SECTIONS AS THE LAST STAGE 0.300       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  1 0.250       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  2 0.200       0.400                MAX THICKNESS AND ITS LOCATION FOR ROTOR   1 SECTION No.  3 y STATOR No.  2 SET ANSTK= "Y" TO CHOOSE THE SAME BLADE SECTIONS AS THE LAST STAGE. y ROTOR No.  2 SET ANSTK= "Y" TO CHOOSE THE SAME BLADE SECTIONS AS THE LAST STAGE. 

**==> picture [324 x 186] intentionally omitted <==**

**==> picture [34 x 35] intentionally omitted <==**

**==> picture [106 x 26] intentionally omitted <==**

This file, produced by answering questions on the screen. 

(Only the numbers and characters on the left are input) 

Produces this Turbine 

**82** 

## STAGEN 

Reads in a data file produced by MEANGEN. 

- ➢ Allows the blade sections to be changed from the initial crude guess. 

- ➢ Projects the blades onto quasi-stream surfaces. 

- ➢ Stacks the blades. 

- ➢ Generates the grid. 

- ➢ Combines the blades into stages. 

- ➢ Writes an input data file for MULTALL . 

As with MEANGEN many parameters are set by default and can be changed by editing the program. 

The blade profiles may be either: 

- Generated from a system of equations. 

- Generated from an input camber line and thickness distribution. 

- Read in from an existing profile. 

**==> picture [87 x 35] intentionally omitted <==**

**83** 

## Blade thickness distributions from equations. 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [214 x 265] intentionally omitted <==**

Root, mid and tip blade sections generated for an LP steam turbine last rotor. 

**84** 

## MULTALL 

## 3D multistage N-S solver developed over many years. Using on a finite volume time-marching method. 

## It can model most turbomachinery flow features, including: 

- Mixing plane model between blade rows. 

- Quasi-3D blade-to-blade calculations. 

- Axisymmetric throughflow calculations. 

- Three turbulence models. 

- Specified boundary layer transition point, or a simple transition model. 

- • Surface roughness effects. 

- Cooling flow addition through the blades or endwalls. 

- Bleed flows from the hub or casing. 

- Artificial compressibility for low Mach number and incompressible flows. 

- Pinched tip model for plain tip clearances. 

- Shroud leakage model for shrouded blades. 

- Temperature dependent gas properties. 

- Automatic matching of the grids at the mixing plane. 

- Ability to refine the grids within the code. 

- Automatic trailing edge cusp generation. 

- Modification of the inlet boundary conditions to simulate a repeating stage. 

- Ability to perform limited blade redesign within the 3D code. 

**==> picture [87 x 35] intentionally omitted <==**

Most of these are briefly described in the paper, and in detail in the user manual, but there is no time to describe them here. 

**85** 

MULTALL uses a simple “H” grid, which is extremely simple to generate and is anyhow always necessary at mixing planes. However, use of an “H” mesh is much disapproved of by CFD specialists because of numerical errors on highly sheared cells. 

However, using cell corner storage of the variables, MULTALL works remarkably well on sheared grids, its speed and simplicity allow more cells to be used in highly sheared regions. 

Turbine leading edge stagnation point 

**==> picture [283 x 193] intentionally omitted <==**

Comparison with the exact solution on a 60deg staggered wedge. Inlet Mach number =1.6. 

**86** 

## MULTALL uses mixing planes between blade rows in relative motion. 

The mixing plane model has been refined over many years. There are two coincident pitchwise grid lines at the mixing plane. The flow quantities are extrapolated onto these lines and the flow between them is matched by a 1D timemarching procedure. 

**==> picture [87 x 35] intentionally omitted <==**

**87** 

The mixing plane should allow pressure waves to intersect it without reflection and should mix out a potential flow without any loss. The flow downstream of it should have pitchwise uniform entropy and relative stagnation enthalpy. 

**==> picture [296 x 367] intentionally omitted <==**

**==> picture [320 x 313] intentionally omitted <==**

**88** 

**==> picture [336 x 243] intentionally omitted <==**

Entropy contours, the entropy is pitchwise uniform immediately downstream of the mixing plane. 

Entropy changes at a mixing plane. 

**==> picture [150 x 13] intentionally omitted <==**

The mass averaged entropy increases at the mixing plane as required for the mixing loss. 

Axial distance 

**89** 

## MULTALL can be run as a quasi-3D blade-to-blade solver by setting a single cell in the spanwise direction. 

**==> picture [233 x 138] intentionally omitted <==**

Any flow across the imaginary mid-cell line generates a pressure difference between the two end walls which keeps the flow on the stream surface. 

Run times are of order 5-10 seconds per blade row. 

**==> picture [254 x 204] intentionally omitted <==**

**==> picture [234 x 200] intentionally omitted <==**

**==> picture [232 x 201] intentionally omitted <==**

45deg flare + 20% radius change. 

2D cascade. Constant stream surface thickness. 

Constant radius + 25% SS divergence. 

Same compressor blade row with different stream surfaces 

**==> picture [87 x 35] intentionally omitted <==**

**90** 

## THROUGHFLOW CALCULATIONS 

The code can be run as an axisymmetric throughflow calculation by setting a single cell in the pitchwise direction. 

The full 3D geometry is input but far fewer grid points can be used. 

**==> picture [195 x 199] intentionally omitted <==**

As with the B-to-B method, any flow crossing the imaginary mid-passage line is made to increase the pressure on one blade surface and decrease it on the other. This gradually builds up a blade loading which keeps the flow on the mid-passage line. Deviation and incidence to the mid-passage line are added. 

Although the blade loading calculated in this way is only a rough approximation to the true loading its overall magnitude is compatible with the momentum change. 

**==> picture [87 x 35] intentionally omitted <==**

**91** 

**==> picture [263 x 196] intentionally omitted <==**

**==> picture [270 x 207] intentionally omitted <==**

LP Steam turbine. Streamlines. Full 3D . 

~~LP Steam turbine~~ Streamlines. Throughflow. 

**==> picture [253 x 211] intentionally omitted <==**

**==> picture [328 x 232] intentionally omitted <==**

LP steam turbine, blade surface pressure distributions from throughflow. 

~~Comparison of throughflow and full 3D Mac~~ h numbers in LP steam turbine. 

**==> picture [87 x 35] intentionally omitted <==**

**92** 

## Its advantages over conventional (streamline curvature) throughflow methods are: 

- It gives a crude estimate of blade loading. 

- It predicts the 3D effects of blade stacking. 

- The stability is not limited by the grid aspect ratio. 

- It predicts viscous losses on all solid surfaces via a very simple skin friction model. 

- • It predicts tip leakage flows and losses. 

- It predicts the growth of endwall boundary layers, but not the associated secondary flows. 

- It works with a specified exit pressure rather than a specified mass flow. 

- It works with choked blade rows, including predicting supersonic deviation. 

- It predicts normal shock waves but not oblique shocks. 

- It is very easy to change from throughflow to full 3D calculation – change 2 lines of data. 

## Its disadvantages are: 

- It does not work in the inverse (design) mode. 

- Run times are 5-10 seconds per blade row rather than a fraction of a second with streamline 

- curvature. 

- It requires a blade shape, although this can initially be a simple guess. 

- It does not give realistic pressure distributions for transonic compressors, but nor does any 

- throughflow method. 

- Users are not so familiar with the method. 

**==> picture [87 x 35] intentionally omitted <==**

**93** 

## EXAMPLE OF USE OF THE DESIGN SYSTEM 

## Specify a large axial compressor with: 

Mass flow rate  50kg/s Stagnation pressure ratio = 2.0 Rotational speed = 5000 rpm Constant tip diameter = 1m Ambient inlet conditions 1bar, 300K . 

Assuming an isentropic efficiency = 90% , a 3 stage machine with a moderate stage loading coefficient = 0.36 should satisfy the requirement. 

o The inlet Mach number at the tip would be near sonic so to reduce this 15 of inlet swirl is chosen. This is gradually reduced so there is no swirl at exit. 

Run MEANGEN with specified inlet and outlet absolute flow angles (different for each stage), flow coefficient = 0.6, loading coefficient = 0.35. Design on the tip stream surface. 

Initially use a fairly coarse grid, 37x105x37, points per blade row.  No tip clearance or hub seal leakage. 

**==> picture [87 x 35] intentionally omitted <==**

**94** 

For the initial runs make changes only in MEANGEN to get good flow on the design stream surface, no attempt to optimise the blade sections at other radii. 

M Produce an initial layout by running Meangen with default parameters and screen input. The solution has slightly low mass flow and pressure ratio. 

- M Increase the guess of deviation angles to increase the pressure ratio. Increase the blade thickness and blade numbers. Several runs to obtain flow and pressure ratio close to the 

- specified values. 

M The blades are mid-loaded. Move the point of maximum thickness and point of maximum camber forwards to obtain more fore-loaded blades. Reduce the trailing 

edge thickness. Several runs to obtain the required mass flow and pressure ratio. 

- M Move the point of maximum camber slightly further forwards. The blades now have good surface pressure distributions but there are high incidences on some sections. Adjust the average incidence angles for each row. Several runs. 

Total about 12  3D runs. Each run takes about 12 minutes on a single processor. 

**==> picture [87 x 35] intentionally omitted <==**

**95** 

## Results from the FIRST run using MEANGEN alone. 

Meridional view with streamlines 

**==> picture [87 x 35] intentionally omitted <==**

Mid-span Mach numbers 

**96** 

## Now make further changes by editing the STAGEN input file to refine the blade sections and adjust the incidences along the span 

S Change to a finer 55x140x55 point grid with tip gaps on all rotors, 5 cells in each tip gap. Adjust the incidence angles along the span. Rotor 3 is most highly loaded so increase its blade numbers. Several runs. 

- S Add hub shroud leakages on all stators. Adjust incidences. Several runs. 

- S Bow all stators, with pressure surfaces leaned towards the endwalls, to reduce endwall loadings. Re-adjust the incidences. The performance is now very close to specification with a predicted isentropic efficiency of 91.5% . 

- S To improve the stall margin add forwards sweep at all rotor tips by increasing the chord by 15% with a fixed trailing edge location. 

- S Further refine the blade incidences. Several runs. 

- S Run a characteristic from choke to stall. 

- S Run a very fine grid solution, 83x299x83 points per row, at the design point to check for any grid sensitivity. The mass flow and pressure ratio each changed by about 0.1% and the efficiency was 0.4% lower. 

Total about 17 3D runs, each taking about 30 minutes when starting from the previous solution. 

**97** 

## Uniformly loaded blades 

**==> picture [65 x 35] intentionally omitted <==**

**==> picture [432 x 304] intentionally omitted <==**

Pressure ratio and efficiency slightly exceed the design targets 

**98** 

In total the design used about 30  3D runs, requiring about 12 hours CPU time on a single processor of a LINUX desktop (home) computer. 

However, more time than this is necessary for “thinking” about what changes to make next. 

Allowing for this, the design could be completed in about 3 person days. 

**==> picture [87 x 35] intentionally omitted <==**

**99** 

## CONCLUSIONS 

The design system is relatively simple, easy to use and fast to run. 

However, as with any design process, it requires an experienced user to know what geometrical changes are needed to produce the required flow behaviour. Repeated use of the design system is a good way of acquiring such experience. MULTALL is a useful tool in its own right. It is simpler and faster than most CFD codes and some of the techniques used in it may be of use to other CFD developers. 

**==> picture [649 x 175] intentionally omitted <==**

**100** 

The FORTRAN source codes, user manuals and sample data sets can be downloaded as a folder named ‘multall-open’ from ‘dropbox’ using the following link. 

https://www.dropbox.com/sh/8i0jyxzjb57q4j4/AABD9GQ1MUFwUm5hMWFylucva?dl=0 

You do not need a ‘dropbox’ account to access this. 

A brief description of the system and a copy of the link is also available on the web site 

https://sites.google.com/view/multall-turbomachinery-design 

Any future developments to the programs or changes to the link will be announced on this web site. 

**==> picture [87 x 35] intentionally omitted <==**

**101** 

## 10 stage compressor with overall pressure ratio 10:1 

**==> picture [372 x 306] intentionally omitted <==**

**==> picture [582 x 127] intentionally omitted <==**

**102** 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [259 x 291] intentionally omitted <==**

Low Mach number flow around a cascade of cylinders. Maximum Mach number = 0.08. 

**==> picture [303 x 260] intentionally omitted <==**

**103** 

**==> picture [518 x 323] intentionally omitted <==**

Flow in a water pump. Contours of relative velocity. 

**==> picture [87 x 35] intentionally omitted <==**

**104** 

**==> picture [125 x 540] intentionally omitted <==**

## **Appendix** 

# **Basics on CFD for turbomachinery** 

Acknowledgements: A. Rubino - See also: http://www.cfd online.com/Wiki/Best_practice_guidelines_for_turbomachinery_CFD 

**105** 

## Hierarchy of CFD models 

**==> picture [720 x 330] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

106 

## Multi-row simulation methods 

**==> picture [720 x 229] intentionally omitted <==**

**----- Start of picture text -----**<br>
Multall<br>**----- End of picture text -----**<br>


**==> picture [87 x 35] intentionally omitted <==**

107 

## Throughflow simulations 

- Loss and deviation correlations. 

- Accuracy determined more by correlations than by numerical method. 

- Assumptions: – Circumferentiallyaveraged flow. 

- – Axisymmetric. 

**==> picture [347 x 185] intentionally omitted <==**

**==> picture [349 x 185] intentionally omitted <==**

**==> picture [87 x 35] intentionally omitted <==**

108 

## Mixing-plane simulations 

**==> picture [364 x 154] intentionally omitted <==**

- Instantaneous mixing at mixing plane. 

• Non-uniform flow after mixing plane (conservation of mass, momentum and energy). 

**==> picture [309 x 233] intentionally omitted <==**

- Low computational cost. 

- Use for efficiency estimation. 

**==> picture [87 x 35] intentionally omitted <==**

109 

## Frozen-rotor simulations 

- Rotor kept frozen with respect to stator. 

- Results depend on relative position rotor-stator. 

- If pitch ratio between rotorstator not integer, periodic BCs cannot be applied because of temporal lag. Use phase-lag periodic BCs. 

- Use to initialize unsteady computations with sliding mesh. 

- Used for interaction simulations between vaned and vaneless turbomachinery components (rotor-diffuser, impeller-volute, inlet-impeller). 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [327 x 203] intentionally omitted <==**

**==> picture [243 x 203] intentionally omitted <==**

110 

## Sliding-mesh URANS simulations 

- Unsteady simulations. 

- Sliding motion between stationary and rotating mesh. 

- URANS as most accurate method for blade row calculations in industry. 

- High cost and memory requirements (not used for design optimization). 

- • Initialize using a steady solution. 

**==> picture [87 x 35] intentionally omitted <==**

**==> picture [291 x 185] intentionally omitted <==**

**==> picture [293 x 257] intentionally omitted <==**

111 

## Reduced Order Methods (ROM): Harmonic Balance 

- Unsteady simulations with a- priori known discrete set of frequencies (periodic phenomena). 

- Unsteady solution only for blade passing frequency harmonics. 

- Reduced computational cost, use for unsteady optimization. 

- • Possible numerical stability problems. 

- No initial transient as with URANS. 

- For >10 frequencies, computational cost can exceed URANS. 

- Stator-rotor interaction (known harmonics). 

**==> picture [174 x 223] intentionally omitted <==**

**==> picture [274 x 210] intentionally omitted <==**

112 

## Limitations of CFD for turbomachinery 

- Difficult prediction: 

   - Boundary layer transition. 

   - Turbulence. 

   - Endwall losses. 

   - Leakage flows. 

   - Leading-edge flow in compressors. 

   - Trailing-edge flow in turbines. 

- Modelling challenges: 

   - Geometrical details. 

   - Boundary conditions. 

   - Freestream turbulence. 

   - Endwall boundary layers. 

- Check convergence, physical sense, required information. 

**==> picture [87 x 35] intentionally omitted <==**

113 



# --- END OF SOURCE: Multall Tutorial 2023.pdf ---



# ========================================================
# START OF SOURCE: new-readin-input-data-20.9 .pdf (Category: Multall Documentation)
# ========================================================

## **DATA INPUT FOR THE PROGRAM MULTALL_OPEN USING   “NEW_READIN”** 

UPDATED FOR VERSION MULTALL-OPEN-20.9  .   November 2020. 

## **IMPORTANT NOTE.** 

MULTALL_OPEN can use either of two different input files. 

One is closely the same as used in previous versions of MULTALL and is read by subroutine OLD_READIN. The data for this is mainly formatted, which means all data values must be in the correct columns and any value not present will be taken as zero. The data requirements for this are described in the manual “old-readin-input-data.doc”. 

The other is thought to be a more rational layout of the data and is read by subroutine NEW_READIN. The data input for this is all free format, that means that a value must be present for every number being input, if a value is not present the next value will be taken, even if it is on a different line, and this will almost certainly cause an error. The details of this input type are described in this manual. 

The program decides which form of input to use by reading a file named “intype”  which contains the single character “N”  or “O”  for “new” and “old” READIN respectively. The file “intype”  must be in the same directory as that from which the program is being run. 

All data for NEW_READIN is in **Free Format** which means that there must be at least one space between adjacent numbers and that all numbers in a list must be present.  If any value in a list is missing then the next value will be taken, even if it is on the next line of data, and this will almost certainly lead to an error.  However, many lines of data can be set by default and this option is chosen replacing the appropriate line of numeric data by any alphabetic character, e.g. by “D”  . 

Each line of data is referred to as a “CARD” which is a legacy from the time when the data was input on punched cards, as it was at the start of development of this program in the mid ‘70’s  . 

Many lines of data are be preceded by a comment line describing the data to be input in the next line. These are included to help in identifying each line of data. These comment lines can contain any alphanumeric characters but must not be more than 72 characters long. Such comment lines are referred to as **CARD XXdescription** in the following description of the data input, so whenever **CARD XXdescription** and **CARD XX** are called for, two lines of data are required with the first line a comment line and the second line containing the required data. 

More details of the input data options are given in the section entitled NOTES, which follows the end of the input data description. 

## **IMPORTANT NOTE** 

The inverse mode in MULTALL_OPEN_20.6 is only available if using the NEW_READIN input data format. This is also the case if using IFGAS = 3 to use the “lookup-table” input for fluid properties. 

IFGAS = 3 is new to version 20.9. If it is used then a separate input file entitled “props_table.dat”  is read in. This must be in the same directory as the program being run.. The data requirements for this are described in a separate document entitled “readin_table_option.doc” in this folder. 

## **CARD LIST** 

*************************************************************************** 

## **CARD 1** 

TITLE 

TITLE Is a title for the run, up to 72  alphanumeric characters in length. 

There are no defaults for this line of data. 

*************************************************************************** 

## **CARD  2description  and 2** 

CP, GA, IFGAS 

CP Gas specific heat capacity in J/Kg K. e.g. CP  = 1005  for air .  Set any negative value to use real gas properties. GA Gas specific heat ratio , e.g. = 1.4 for air. IFGAS Set IFGAS = 0 for a perfect gas, = 1 for real gas with Cp dependent on temperature and = 3 to use a lookup table for gas properties. 

NOTE  IFGAS is new to version 20.9 . If IFGAS = 3 then a separate file entitled “props_table.dat”  must be read in from unit 9. A description of the required data and format of this file is provided in the document  “readin_table_option.doc” in this folder. 

Also if IFGAS = 3 then stagnation enthalpy must be input instead of stagnation temperature in CARD 77. 

The above values are chosen as defaults if this card is a single alphabetic character, e.g.  “D”. The value of IFGAS defaults to 0 if it is not input. 

************************************************************************** 

## **CARD 3 This is only required if CP in the previous card was negative.** 

CP1, CP2, CP3, TREF, RGAS 

CP1 The value of CP  at TREF in J/kg K CP2 The rate of change of CP with temperature at  TREF CP3 The second derivative of the variation of CP with temperature at TREF. TREF The reference temperature in degrees K . RGAS The constant value of gas constant in J/kg k. 

The specific heat is taken to vary as: 

**==> picture [323 x 21] intentionally omitted <==**

For combustion products typical values are  TREF = 1400, CP1 = 1272.5,  CP2  = 0.2125, CP3  =  0.000015625,   RGAS = 287.5. 

The above values are chosen as defaults if this card is a single alphabetic character, e.g.  “D”. ************************************************************************** 

## **CARD  4description  and 4.** 

## ITIMST 

ITIMST defines the type of timestep to be used. 

= 3-> Non-uniform time steps updated as a function of Mach number using the basic “scree” scheme.  This is the standard option. = 5-> Low speed flow using an artificial speed of sound. Use this if the maximum Mach number is less than about 0.25. Extra data is then needed in CARD 6. = 6-> Fully incompressible flow with constant density. Extra data is then needed in CARD 7. 

= 4  or -4 ->The SSS scheme is used with the values of F1, F2 and F3  input as data in card 5 . 

If the values of ITIMST are  negative,  -3, -5 or -6 , then the options are as with the same positive values described above, but the SSS scheme with standard coefficients is used. This should allow larger CFL numbers, up to 0.75 or more, but is sometimes less robust. 

ITIMST = 3 is the usual option but = -3 may allow larger CFL numbers and so give faster convergence. See Note 3  for more details. 

There are no defaults for this data. 

************************************************************************** 

## **CARD 5 Only needed if ITIMST in Card 4  was =  4 or -4 .** 

F1, F2EFF, F3, RSMTH, NRSMTH 

F1, F2EFF, F3      Coefficients of the SSS scheme. Standard values are  F1= 2.0,  F2EFF = -1.0, F3 = -0.65 . RSMTH Residual smoothing factor, Standard value = 0.4 NRSMTH Number of residual smoothing passes. Standard value= 1. 

See Note 3 for more details of the SSS scheme. 

There are no defaults for this data. 

************************************************************************** 

## **CARD 6 Only needed if ITIMST in Card 4 was = 5 or -5 .** 

VSOUND,  RF_PTRU,  RF_VSOUND, VS_VMAX 

VSOUND An initial guess of the artificial speed of sound. It should be about twice the expected maximum relative velocity. It is only an initial guess and is automatically changed by the VS_VMAX ratio during the calculation. Default = 150 m/s . 

RF_PTRU A relaxation factor on the changes in the calculated pressure. Typical value =  0.01  . 

RF_VSOUND  A relaxation factor on the changes in the calculated artificial speed of sound. Typical value =  0.002  . VS_VMAX The ratio of the calculated sound speed to the calculated maximum flow speed. Typical value = 2.0  . 

Defaults are as given above. See Note 18  for more details of the low Mach number scheme. 

## **CARD 7 Only needed if ITIMST in CARD 4 was = 6 or -6 .** 

VSOUND, RF_VTRU,  RF_VSOUND, VS_VMAX  , DENSTY 

VSOUND An initial guess of the artificial speed of sound. It should be about twice the expected maximum relative velocity. It is only an initial guess and is automatically changed by the VS_VMAX ratio.  Default = 150 m/s . 

RF_VTRU A relaxation factor on the changes in the calculated pressure. Typical value =  0.01  . 

RF_VSOUND   A relaxation factor on the changes in the calculated artificial speed of sound. Typical value =  0.002  . VS_VMAX The ratio of the calculated sound speed to the calculated maximum flow speed. Typical value = 2.0  . DENSTY The fixed value of density for the incompressible flow. The default value is  1.2 kg/m[3] , a typical value for air. 

The defaults are as given above . See Note 18 for more details of the low Mach number scheme. *************************************************************************** 

## **CARD 8description  and  8** 

CFL, DAMPIN, MACHLIM, F_PDOWN 

CFL The CFL number which determines the length of time step. Standard vale = 0.4 for the Scree scheme but higher values up to 0.75 may be possible with the SSS scheme. DAMPIN The damping factor which limits the ratio of maximum change to the average change per time step. Standard value = 10.0  . Higher values, e.g. 25.0, may give faster convergence but are less stable. MACHLIM The maximum relative Mach number is limited to this value. Typical value = 2.0 . The calculation should not fail but may not converge fully if the maximum Mach number exceeds this value. F_PDOWN The pressure may be downwinded to prevent overshoots and undershoots at strong shock waves.  Standard value = 0.0 but set = 0.1 if more shock smearing is required. 

Defaults are as given above. 

See Notes 3  and 5  for more details . 

*************************************************************************** 

## **CARD 9description  and 9** 

IF_RESTART, IF_INV IF_RESTART If  = 0 then start the calculation from an initial guess of the flow field. If  = 1    then start the calculation from a previous solution which has been saved in a file named “flow_out” . 

IF_INV Use the Q3D inverse design mode if IF_INV = 1, Do not redesign if = 0. Default = 0. If IF_INV = 1 then the file “inverse.in” must also be input.  IF_INV is only available in version 20.6. 

Default is  IF_RESTART = 0., IF_INV = 0. 

Starting from a restart file should give faster convergence. 

Note that the file  “flow_out” is always written when convergence or maximum iterations are reached and is also used as the plotting file. 

*************************************************************************** 

## **CARD 10description  and 10** 

NSTEPS_MAX,  CONLIM 

NSTEPS_MAX  The maximum number of time steps before the calculation will be stopped. The value depends on the case but 3000 is usually enough for a single blade row, 5000 for a single stage and up to 10000 for a multistage calculation. More than 10000 time steps should never be needed. CONLIM The convergence level defined as the average percentage change in velocity per time step divided by the RMS velocity of all grid points. Typical value = 0.005 

. Note that CONLIM is the **percentage** change so the usual convergence limit is very tight. 

Defaults are  NSTEPS_MAX = 5000, CONLIM = 0.005 

*************************************************************************** 

## **CARD 11description  and 11** 

SFXIN,  SFTIN, FAC_4TH,  NCHANGE 

SFXIN The smoothing factor in the streamwise (J) direction. Standard value =0.005 . SFTIN The smoothing factor in the pitchwise (I) and spanwise (K) directions. Standard value =0.005 . FAC_4[TH] The proportion of fourth order smoothing.  The second order smoothing used is (1-FAC_4[th] ) x SFXIN  and the fourth order smoothing used is FAC_4[th] *SFXIN . The same for SFTIN. Typical value = 0.8 . NCHANGE The smoothing factors and damping are increased at the start of the calculation and are gradually decreased to the values set above over NCHANGE steps. Typical value = NSTEPS_MAX/4 . 

Defaults values are  as given above. 

*************************************************************************** 

## **CARD  12description and 12** 

NROWS 

NROWS The number of blade rows to be calculated. The limit is only imposed by the dimensioning of the program. The current limit is 26.  Edit “commall-open“ if this needs to be increased. 

There is no default value for this data since NROWS will vary from case to case. *************************************************************************** 

## **CARD 13description and 13** 

IM , KM 

IM The number of grid points in the pitchwise direction. This is the same for all blade rows. A typical value = 46. Fewer points, e.g. 28, will give faster run times, more points e.g. 64, will give greater accuracy. The current limit as set by the dimensions of “commall-open” is 83. KM The number of grid points in the spanwise direction. This is the same for all blade rows. A typical value = 46. Fewer points, e.g. 28, will give faster run times , more points e.g. 64, will give greater accuracy. The current limit as set by the dimensions of  “commall-open” is 83. 

There are no default values for these two numbers since they will vary from case to case. *************************************************************************** 

## **CARD 14description   and 14** 

FP(I), for  I = 1,IM-1 

FP(I),   I=1 to IM-1 FP(I)  are the relative grid spacings in the pitchwise direction.  IM-1 values must be input.  If FP(3)  is set to zero then the spacings are generated automatically as a geometric progression with expansion ratio FP(1)  and maximum spacing ratio = FP(2) . These are applied away from both blade surfaces.  Typical values are FP(1) = 1.25, FP(2) = 10.0 , FP(3) = 0.0.   All the remaining  IM-4  values must still be input but they are not used. 

Note that these are the relative spacings so that only their ratios matter, their absolute values do not matter.  A higher expansion ratio and a larger ratio of maximum to minimum spacing will give more grid points in the boundary layers. However, it is recommended that the expansion ratio should not be greater than 1.3  as large values will generate numerical errors. 

It is usually more convenient to use the option to generate the spacings automatically but data must still be input for the  IM-4 points that will not be used. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 15description and 15** 

FR(K), for K = 1,KM-1 

FR(K),   K=1 to KM-1      FR(K) are the relative grid spacings in the spanwise direction.  KM-1 values must be input.  If FR(3) is set to zero then the spacings are generated automatically as a geometric progression with expansion ratio FR(1) and maximum spacing ratio = FR(2) . These are applied away from both endwalls.  Typical values are FR(1) = 1.25, FR(2) = 10.0 , FR(3) = 0.0 .   All the remaining KM-4 values must still be input but they are not used. 

Note that these are the relative spacings so that only their ratios matter, their absolute values do not matter.  A higher expansion ratio and a larger ratio of maximum to minimum spacing will give more grid points in the boundary layers. However, it is recommended that the expansion ratio should not be greater than 1.3  as large values will generate numerical errors. 

It is usually more convenient to use the option to generate the spacings automatically but data must still be input for the  KM-4 points that will not be used. 

The spacings are automatically adjusted to accommodate the specified tip gaps. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 16description and 16** 

## IR, JR, KR, IRBB, JRBB, KRBB 

IR 

The block size of the smallest multigrid blocks in the I direction. Typically IR = 3 .  Set IR = 1  if performing a throughflow calculation. 

JR The block size of the smallest multigrid blocks in the J direction. Typically JR = 3. 

KR 

The block size of the smallest multigrid blocks in the K direction. Typically KR = 3. Set KR = 1 if performing a quasi-3D blade –to-blade calculation. 

IRBB The block size of the second level of multigrid blocks in the J direction. Typically IRBB = 9. Set = 1 if IR = 1. 

JRBB The block size of the second level of multigrid blocks in the J direction. Typically JRBB = 9. 

KRBB The block size of the second level of multigrid blocks in the K direction. Typically KRBB = 9. Set = 1 if KR = 1. 

The default values are the typical ones given above. However, there is no need to use these exact values. Larger block sizes may give faster convergence but are more likely to need lower safety factors, see card 17. 

It is desirable, but not essential, that there are a whole number of blocks across the pitch and span. So, if IR = 3  and IRBB = 9, good values for IM  would be 19, 28, 37, 46, 55, and 65 . Similarly for KM. 

If IM was = 2  to specify a throughflow calculation, then IR and IRBB must = 1. 

If KM was = 2 to specify a Q3D blade-to-blade calculation, then KR and KRBB must = 1. 

In addition to these two block sizes there is a third level of multigrid for which the blocks cover the whole span and whole pitch with one block upstream of the leading edge, 2 blocks within the blade passage, and one block downstream of the trailing edge. i.e. only 4 blocks per blade row. These “superblocks” are generated automatically with no user input. 

The default values are as given above. 

*************************************************************************** 

## **CARD 17description  and 17** 

FBLK1, FBLK2, FBLK3 

FBLK1 The safety factor on the time step length for the first level of multigrid blocks.  Typical value = 0.4 . FBLK2 The safety factor on the time step length for the second level of multigrid blocks. Typical value = 0.2 . FBLK3 The safety factor on the time step length for the third level of multigrid blocks, Typical value = 0.1. 

These safety factors are the ratio of the CFL number used for the block to the theoretical limiting value. The defaults are the values suggested above.  Larger values will give faster convergence but may lead to instability. 

*************************************************************************** 

## **CARD 18description  and 18** 

IFMIX 

IFMIX Set IFMIX= 1 if a mixing plane is to be used. Set = 0 if there is no mixing plane. 

The default is IFMIX = 1. It is very unlikely that a mixing plane will not be used when there is more than one blade row. 

************************************************************************** 

## **CARD 19description and 19 .   Only needed if IFMIX (card 18) is not 0 .** 

RFMIX, FEXTRAP, FSMTHB, FANGLE 

RFMIX The relaxation factor on the isentropic forcing downstream of the mixing plane. Typical value = 0.025 , reduce this if there is any sign of instability at the mixing plane. FEXTRAP The factor by which the flux is extrapolated from upstream of the mixing plane to the mixing plane. Typical  value = 0.8 but use a larger value for close grid spacings. FSMTHB The factor scaling the special smoothing upstream and downstream of the mixing plane. Typical value 1.0 . FANGLE The factor by which the flow direction is extrapolated from downstream to the mixing plane. Typical value = 0.8 but use a larger value for closer grid spacings. 

See Note  17 for more details of the mixing plane treatment. Use larger values of FEXTRAP and FANGLE, e.g.  0.95,  if the streamwise grid spacing is very small at the mixing plane. The value of FSMTHB does not seem to be very important. 

The default values are those given above. 

************************************************************************** 

## **CARD 20description  and 20** 

## IFCOOL, IFBLEED, IF_ROUGH 

IF COOL Set = 1 or 2 if any cooling flows are to be included on any blade row. IFCOOL = 1 gives a uniform coolant flow over the patch with the velocity determined by the input value of Mach number. The input value of stagnation pressure is not used except to calculate the efficiency.  IFCOOL = 2 allows the coolant velocity to vary over the patch as determined by the local static pressure and the input stagnation pressure. The input value of Mach number is not used. Set IFCOOL = 0  if there are no cooling flows. Default = 0 . 

IF BLEED Set = 1 if there are bleed flows from the hub or casing of any blade row. Set = 0  if there are no bleed flows. Default = 0 . IF_ROUGH Set = 1 if any surface of any blade row is to be treated as rough.  Set = 0 if all surfaces of all blade rows are smooth. Default = 0. 

Defaults are as given above. Further input is needed later in Cards 86 and in the sections entitled   COOLING FLOWS and BLEED FLOWS at the end of the input data if any of these are non-zero. 

*************************************************************************** 

## **CARD 21description  and 21** 

NSECS_IN 

NSECS_IN The number of quasi stream surfaces on to which the input blade geometry will be interpolated. This is the same for all blade rows. The interpolation is done before generating the final grid. NSECS_IN is usually the same as the number of input stream surfaces, (NSECS_ROW,  Card 51) but they need not be the same. 

If the number of input stream surfaces is not the same for all blade rows then set NSECS_IN equal to the largest number of input surfaces. It is usually more convenient to have NSECS_IN  = NSECS_ROW and with the same value for all blade rows. 

Note that there is no default value for this data. *************************************************************************** 

## **CARD 22description  and 22** 

IN_PRESS, IN_VTAN, IN_VR, IN_FLOW, IF_REPEAT, RFIN 

IN_PRESS Determines how the pressure is extrapolated to the inlet boundary. Usual value = 0 so the pressure is calculated from the density which is solved for by the continuity equation. If =1 the inlet pressure is extrapolated from the interior flow field. If = 3 the pitchwise averaged pressure is extrapolated. If = 4 the passage average pressure is extrapolated. See Note 1 for more details. 

- IN_VTAN 

   - Determines the boundary condition on the inlet tangential velocity or flow angle. Set = 0 if the absolute flow angle is fixed, set = 2 if the relative flow angle is fixed, set = 1 if the absolute tangential velocity is fixed. See Note 1 for more details. 

- IN_VR Determines the boundary condition on the inlet radial velocity. Set  = 0 if it is extrapolated from the downstream flow field. Set = 1 if the radial velocity is determined by a fixed meridional pitch angle which is input in Card 81. If IN_VR = 1 the pitch angle specified must be  compatible with the slopes of the hub and casing at inlet. 

- IN_FLOW 

   - Determines whether to try to force a specified mass flow rate. Set = 0 if no mass flow forcing. Set = 2  to force the local flow towards the current average flow. Set = 3 to force the flow towards an input value which is input in Card 26. See Note 11 . This option is seldom used so the usual value = 0. 

- IF_REPEAT Determines whether to force a repeating stage condition at the inlet boundary.  Set = 0  for no repeat condition, which is most usual. Set = 1 to use the repeating flow condition in which case extra data will be read in Card 27 . 

- RFIN 

The relaxation factor on changes in the inlet pressure. The value depends on the choice of IN_PRESS. If  IN_PRESS = 0 then set = 0.5.  For other choices of IN_PRESS set = 0.1. Reduce if there are any signs of instability at the inlet boundary. See note 1 for more details. 

The defaults values are:  IN_PRESS = 0, IN_VTAN = 0, IN_VR = 1, IN_FLOW = 0, IF_REPEAT = 0, RFIN = 0.5  . 

*************************************************************************** 

## **CARD 23description  and 23** 

IPOUT,  SFEXIT,  NSFEXIT, FP_EXTRAP,  FRACWAVE 

FRACWAVE  and FP_XTRAP  are new to version MULTALL_OPEN_19.2.F 

## IPOUT 

Determines the boundary condition on the exit static pressure. IPOUT = 0 means that the pressure is fixed as PDHUB on the hub and simple radial equilibrium is imposed. IPOUT =  -1  means the pressure is fixed as PDTIP on the casing and simple radial equilibrium is imposed. IPOUT = +1 means the exit pressure is fixed at all spanwise positions with a linear variation between the input values PDHUB  and PDTIP.  IPOUT = +3  means that the spanwise exit pressure variation is read in as data in Card 76 . 

- SFEXIT A factor for smoothing the exit flow field. If SFEXIT is not zero this is smoothed in both the pitchwise and spanwise directions. It is usually only used when there is instability due to the flow trying to reverse at the exit boundary in which case set SFEXIT = 0.1  and NSFEXIT = 5 -> 10. Increase these to apply a more powerful smoothing. Most usually SFEXIT = 0.0 . 

- NSFEXIT The smoothing is applied over NSFEXIT points upstream of the exit boundary. Typically = 5  but increase it to apply a more powerful smoothing over more mesh points. 

- FP_EXTRAP The fraction by which the pressure is extrapolated to the downstream boundary. Typical value = 0.9 . This is also used when FRACWAVE = 0  so the original boundary condition is used. Reduce the value if there is instability at the downstream boundary. 

- FRACWAVE The fraction of the required change in pitchwise average exit pressure that is added on each time step. The pressure is added as a one-dimensional wave which changes the density, velocity and energy as well as the pressure. Typical value = 0.25 but reduce if there are any signs of instability at the downstream boundary. 

   - The new boundary condition is used if FRACWAVE is greater than zero. If it = zero or if it is not included in the data set then the original exit boundary condition is used. The options IPOUT = -1, 0 ,+1  or +3  can still be used with the new exit boundary condition. 

Defaults are IPOUT = 1, SFEXIT = 0.0, NSFEXIT = 0 , FP_EXTRAP = 0.9, FRACWAVE = 0.0  See Note 2 for more details of how IPOUT is used 

************************************************************************** 

## **CARD 24description  and 24** 

PLATE_LOSS, THROTTLE_EXIT 

PLATE_LOSS The loss coefficient of a simulated perforated plate or wire mesh screen at the exit boundary. This may be used to make the exit flow more uniform if there is a tendency for it to reverse at exit. It works by increasing the static pressure upstream of the simulated plate by PLATE_LOSS x (  ρ Vm2- (ρ Vm2 )mid ) .  A value = 2.0 should make a non-uniform flow closely uniform.  The use of SFEXIT is usually a better way of preventing reverse flows and so this option is not usually needed, hence PLATE_LOSS usually = 0.0 . 

THROTTLE_EXIT Simulates a throttle downstream of the calculated region. The exit pressure is made to vary with exit mass flow rate so it lies on a parabolic curve passing through THROTTLE_PRES and THROTTLE_MAS both of which are input in the next card. This is useful for calculations on compressors near their stall point. The solution found should lie at the intersection of the compressor’s static pressure to mass flow characteristic and the parabolic curve through these points. Set THROTTLE_EXIT = 1.0  to use this option. Set = 0.0 if this option is not used as is most usual unless near the stall point. 

Defaults are PLATE_LOSS = 0, THROTTLE_EXIT = 0   so the option is not used . *************************************************************************** 

## **CARD 25 . This card is only needed if THROTTLE_EXIT in Card 24 is not zero.** 

THROTTLE_PRES,  THROTTLE_MAS,  RF_THROTL 

THROTTLE_PRES The exit pressure is made to vary with exit mass flow rate along a parabolic curve passing through the point THROTTLE_PRESS and THROTTLE_MAS .  In  N/m[2   ] . 

THROTTLE_MAS The mass flow at the point where the exit pressure is THROTTLE_PRES .  In Kg/s . 

RF_THROTL A relaxation factor on changes in exit pressure when using this option. Typical value = 0.1  . 

See Card 24 for details of this option. There are no defaults for this card. *************************************************************************** 

## **CARD 26description  and 26 .** 

## **This card is only needed in  IN_FLOW in card 22 is not zero .** 

FLOWIN, RFLOW 

FLOWIN The required mass flow rate in Kg/s .  This is only used when IN_FLOW =  3. 

RFLOW A relaxation factor on the mass flow forcing. Typical value = 0.1  . 

There are no defaults for this card.  It is very seldom used because IN_FLOW is usually set to zero. 

*************************************************************************** 

## **CARD 27description  and 27.** 

## **Only needed if  IF_REPEAT  in card 23  is  not zero.** 

NINMOD, RFINBC 

NINMOD The inlet boundary conditions are moved towards the repeating stage condition every NINMOD steps. Typically NINMOD =  10. 

RFINBC A relaxation factor on the changes in inlet boundary conditions. Typical value = 0.025 .  Reduce this if there are any signs of instability at the inlet boundary. 

Default values are as given above. 

*************************************************************************** 

## **CARD 28description  and 28 .** 

ILOS, NLOS, IBOUND 

ILOS Determines which viscous model will be used. Set = 0  for an inviscid calculation. Set = 10 to use the original mixing length model, subroutine LOSS. Set  = 100 to use the newer mixing length model, subroutine NEW_LOSS . Set = 200 to use the Spalart-Almaras turbulence model, subroutine SPAL_LOSS . Generally ILOS = 100 is preferred. NLOS The loss subroutine is called every NLOS time steps. Usually NLOS = 5 , lower values may be more stable but will run more slowly, higher values may be less stable but faster.  It is seldom necessary to change the value from 5 . IBOUND Determines whether the endwalls will be treated as viscous or inviscid. If IBOUND = 0, both walls are viscous. IBOUND = 1 makes the hub inviscid, IBOUND = 2 makes the casing inviscid, IBOUND = 3 makes both endwalls inviscid. Usually set IBOUND = 0 . 

Defaults are ILOS = 100, NLOS = 5, IBOUND = 0 . *************************************************************************** 

## **CARD 29description  and 29.** 

## **Only needed if ILOS  in card 28 is not zero.** 

REYNO, RF_VIS, FTRANS, TURBVIS_LIM, PRANDTL,YPLUSWALL 

REYNO If REYNO is greater than 100 it is the Reynolds number of the flow based on the axial chord and the exit relative velocity of the first blade row. This is used to calculate the dynamic viscosity. If REYNO is positive but less than 100 then REYNO = (dynamic viscosity x 10[5] ). If REYNO is negative then Abs(REYNO) x 10[-5] is the dynamic viscosity at a temperature of  T = 288K  and it varies as  (T/288)[0.62] which is a good approximation for air. RF_VIS A relaxation factor on the changes in viscous forces. Usual value = 0.5  and it is seldom necessary to change this. FTRANS A very simple boundary layer transition criterion. The flow is taken to be fully turbulent if the ratio of the maximum calculated turbulent viscosity to laminar viscosity is greater than FTRANS. Set FTRANS = 14 to use this model. However it is not considered very reliable and usually set FTRANS = 0.0 to obtain fully turbulent flow or set FTRANS = 10000. to obtain fully laminar flow. 

TURBVIS_LIM The maximum allowed value of turbulent viscosity is TURBVIS_LIM x the laminar viscosity. Usually set TURBVIS_LIM = 1000 but higher values, up to 3000, may be necessary in multistage machines PRANDTL The Prandtl number of the fluid. Usually set = 1.0. YPLUSWALL If this is greater than 5 then the wall shear stresses are obtained by assuming that the first grid point is at the given value of YPLUS and the original wall functions are not used. If this is done a typical value of YPLUSWALL = 11 .  However, this option is not preferred and usually set YPLUSWALL = 0.0 to obtain the wall shear stresses from the wall functions. In Version 10.5 YPLUSWALL can be used to choose the Shih et al wall functions. If its value is between -10.0  and zero then only the velocity term in these functions is used. This gives results very similar to the original wall function. If its value is less than -10.0 then both the velocity and pressure terms in the Shih et al wall functions are used. The author is dubious of the value of this. 

Defaults are:  REYNO = 500,000 , RF_VIS = 0.5,  FTRANS = 0.0,  PRANDTL = 1.0 , YPLUSWALL = 0.0,  TURBVIS_LIM = 3000. 

*************************************************************************** 

## **CARD  30description  and 30** 

## **This card is only needed if ILOS = 200,  i.e.  if the Spalart-Allmaras (S-A) turbulence model is being used.** 

FAC_STMIX, FAC_ST0, FAC_ST1, FAC_ST2, FAC_ST3, FAC_SFVIS, FAC_VORT,   FAC_PGRAD 

FAC_STMIX A factor which moves the turbulent viscosity calculated by the S-A model towards the mixing length value obtained from NEW_LOSS. Set = 1.0 to use this but usually set = 0.0 . 

FAC_ST0 A scaling factor on the first source term in the S-A model. Standard value = 1.0   but  1.5 is sometimes found to give better results. 

FAC_ST1 A scaling factor on the second source term in the S-A model. Standard value = 1.0  . 

FAC_ST2 A scaling factor on the second source term in the S-A model. Standard value = 1.0  . 

FAC_ST3 A scaling factor on the third source term in the S-A model. Standard value = 1.0  . 

FAC_SFVIS A factor which may be used to increase the smoothing of the turbulent viscosity calculated by the S-A model. Usual value = 2.0 . Higher values are seldom necessary. 

FAC_VORT This is new to version 17.5. It allows the main source term for turbulent viscosity to be increased by streamwise vorticity as suggested by Lee et al in ASME GT201763245 . The increase is limited to (1 + FAC_VORT) x the original source term. Lee et al suggest a value = 0.9191 for FAC_VORT. The default value = 1.0 . So far there is little experience of using this option. 

FAC_PGRAD This is also new to version 17.5. The main source term for turbulent viscosity is increased by adverse pressure gradients, again as suggested by Lee et al. The increase is limit to (1 + FAC_PGRAD) x the original term. Lee et al suggest a value of 0.6565 for FAC_PGRAD. The default value = 1.0 . So far there is little experience of using this option. Both FAC_VORT and FAC_PGRAD can be used together to increase the source term by their product. 

The defaults are as given above. 

*************************************************************************** 

## **CARD 31description  and 31.** 

YPLAM,  YPTURB 

YPLAM Is the value of YPLUS below which the boundary layer is taken to be fully laminar. The usual value = 5.0 . YPTURB Is the value of YPLUS above which the flow is taken to be fully turbulent. Usual value = 25.0  . 

Defaults are as given above.  Between these values the viscosity is blended between the laminar and the calculated turbulent value. These values are only used when there are grid points within the laminar sub layer, YPLUS < 25 ,  otherwise the flow is taken to be fully turbulent or fully laminar as determined by FTRANS . 

*************************************************************************** 

## **CARD32description and 32** 

## **Only needed if IM = 2 to specify a throughflow calculation.** 

Q3DFORCE, SFPBLD, NSFPBLD 

Q3DFORCE A factor scaling the force applied via the blade surface pressure distribution to keep the flow on the stream surface. Usually set = 1.0  but often higher values, sometimes up to 5, can be used and give faster convergence. 

SFPBLD The blade surface pressures are smoothed by SFPBLD. Typical value = 0.1. This high smoothing greatly helps to obtain realistic pressure distributions and improves convergence. 

NSFPBLD The smoothing is applied NSFPBLD times. Typical value = 2. But increase to apply more powerful smoothing. 

Defaults are as given above. See Note 20 for details of the throughflow method. 

*************************************************************************** 

## **CARD 33description  and 33** 

ISHIFT,  NEXTRAP_LE, NEXTRAP_TE 

ISHIFT Determines the type of grid matching between adjacent blade rows. If ISHIFT =  0, the grids input are not changed. If ISHIFT  = 1 the blade rows are moved axially so that the grids coincide at the mixing plane on the hub. If ISHIFT = 2  the grids are moved so that they coincide at the mixing plane over the whole span and maintain the input stream surfaces. ISHIFT = 3  is the same as 2 but makes the grid surfaces conical in the blade to blade gap. ISHIFT = 4  is the same as 3 but do not change the hub and casing grid surfaces. ISHIFT = 2  is usual and is strongly preferred. 

NEXTRAP_LE If the grid direction upstream and downstream of a blade row is obtained by extrapolating the blade centre line then NEXTRAP_LE is the number of the grid points downstream of the leading edge of the point that is used for the extrapolation.  Typical value = 10 . 

NEXTRAP_TE If the grid direction upstream and downstream of a blade row is obtained by extrapolating the blade centre line then NEXTRAP_TE is the number of the grid points upstream of the trailing edge of the point that is used for the extrapolation. Typical value = 10 . 

The defaults are ISHIFT = 2 (which is strongly preferred), NEXTRAP_LE = NEXTRAP_TE = 10 . 

NEXTAP_LE  and NEXTRAP_TE are not used if IF_ANGLES(NR) =1  but values must still be input. 

See note 12 for more details of the grid matching at the mixing plane. 

*************************************************************************** 

## **CARD 34description  and 34** 

NSTAGE(N), N=1, NROWS 

NSTAGE(N) Is the stage number of the Nth blade row. 

There are no defaults for this card as there is no general method of deciding which blade row belongs to which stage. If there is an IGV in front of a compressor stage, or an OGV at exit from a turbine stage,  then that stage should have 3 blade rows. 

*************************************************************************** 

## **CARD 35description  and  35 .** 

NOUT(N) , N = 1 to 5 

NOUT(N) Five values of time step number (NSTEP)  at which an output file “flow_out” will be written. 

This is mainly used when debugging a failed solution when several values of NOUT(N) would be set to give outputs just before failure. 

If NOUT(1) is set to zero (0) then the initial guess of the flow field is sent to the plotting file “flow_out”. This is very helpful in finding errors in the data which cause the program to fail on the first iteration. 

Setting all NOUT by one large number, e.g.  9999999999999999999999999999,  may cause errors on some compilers and so should be avoided. 

An output file is always written at  N = NMAX   or when the convergence limit is reached. 

The default is that all NOUT(N)  > NMAX so it is not used. *************************************************************************** 

## **CARD 36description  and 36.** 

IOUT(I) , I = 1, 13 

IOUT(I) The value of IOUT determines which variables are to be written to the output file “results.out”. If  IOUT(I) = 0, do not write out the Nth variable. If  IOUT(I) = 1 write out the variable on the pitchwise grid lines determined by KOUT(K) which is input in the next card. 

If IOUT(I) = 2 write out a pitchwise mass averaged value of the variable on the grid lines determined by KOUT(K). The variables are numbered as shown below. 

The variables are numbered as follows : 

1 = Percentage change in meridional velocity. 2 = Axial velocity 3 = Absolute swirl velocity 4 = Radial velocity 5 = Static pressure 6 = Relative Mach number 7 = Absolute stagnation temperature 8 = Meridional velocity 9 = Swirl angle tan[-1] (Wq/Vm). 10 = Meridional pitch angle tan[-1] (Vr/Vm) 11 = Density 12 = Ratio of P/ T**(γ/(γ-1)) to the inlet value at mid span and mid pitch. This should =1.0 for isentropic flow and can be thought of as the ratio of the local stagnation pressure to that that would be obtained in an insentropic  process. 13 = Pressure coefficient (P-PIN)/(P01-PIN) 

This option is mainly used for debugging as the files are likely to be too large for visual inspection. The usual choice is to set all IOUT(I) = 0 so no output to “results.out” is obtained. This option can be used in conjunction with KOUT in the next card to limit the amount of output. 

The default is that all IOUT(I) = 0  so there is no output to “results.out” . *************************************************************************** 

## **CARD 37description  and 37.** 

KOUT(K), K = 1,KM 

KOUT(K) KOUT is used to decide on which spanwise (K) grid lines to write output to the file “results.out”. Write output for this K value if KOUT(K) = 1. Do not write if KOUT(K) = 0 . 

The default is that all KOUT(K) = 0  so that there is no output to “results.out”. 

*************************************************************************** *************************************************************************** 

**End of the data which does not depend on the blade row. The following data must be input separately for every row.** *************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **START OF THE DATA INPUT FOR EACH BLADE ROW. RETURN TO THIS POINT AFTER COMPLETING THE DATA FOR ALL BUT THE LAST BLADE ROW.** 

*************************************************************************** *************************************************************************** 

## **CARD  38** 

BLANK CARD This is just used to space out the data. *************************************************************************** 

## **CARD 39 .** 

BLANK CARD This is just used to space out the data. *************************************************************************** 

## **CARD 40 .** 

ROWTYP 

ROWTYP An alphabetic description of the next blade row. e.g. “ROTOR 1 “ . 

*************************************************************************** 

## **CARD 41description and 41 .** 

NBLADES_IN_ROW 

NBLADES_IN_ROW The number of blades in the blade row. 

There is no default value for this card. 

*************************************************************************** 

## **CARD 42description  and 42 .** 

## JMROW, JLEROW, JTEROW 

JMROW The number of streamwise (J index) grid points at which the geometry of the row will be input. The value is the same for all stream surfaces used for input. 

JLEROW The number of the leading edge grid point. JTEROW The number of the trailing edge grid point. 

Note that  JLEROW and JTEROW  are measured relative to the start of this row, not the start of the whole machine. 

There are no default values for this data. 

************************************************************************* CARD 43description  and 43 .** 

KTIPS, KTIPE 

KTIPS The value of the spanwise grid point (K index) at the start of any tip leakage gap. For a hub gap set KTIPS = 1,  for a tip gap set KTIPS equal to the last grid point on the solid blade. Set =  0 if no hub or tip leakage. Set  KTIPS to a negative number to model a shrouded tip seal in which case extra data input is needed in CARDS SHRD1 to SHRD3. 

KTIPE The value of the spanwise grid point at which any tip leakage ends. For a hub gap set KTIPE = the first grid point on the solid blade. For a tip gap set KTIPE = KM . Not used for the shrouded blade model but a value must still be input. 

There are no defaults for these values. 

## **CARD 44description  and 44 .** 

## **These cards are only needed if KTIPS is greater than zero.** 

FRACTIP1,  FRACTIP2 

FRACTIP1 Is the tip clearance as a fraction of the span at the blade leading edge FRACTIP2 Is the tip clearance as a fraction of the span at the blade trailing edge. 

The tip gap is assumed to vary linearly between FRACTIP1  and FRACTIP2 . 

There are no defaults for these values. 

*************************************************************************** 

## **CARD 45description  and 45 .** 

## **This card is only needed if both KTIPS  and KTIPE  are greater than zero. for the current blade row number.** 

FTHICK(K), K=1,KM,  i.e.   KM values. 

FTHICK FTHICK is a factor multiplying the blade thickness so that it can be set to zero in the tip gap. The thickness should be zero at the last point on the blade and all points beyond that. It is usually set = 1.0 for points well away from the tip and gradually reduced to zero over the last few points on the blade. For example, if KT is the value of KTIPS  then FTHICK(KT-3) = 1.0, FTHICK(KT-2) = 0.9, FTHICK(KT-1) = 0.5, FTHICK(KT) = 0.0 and FTHICK = 0.0  for all K > KT  would be typical. 

There are no defaults for these values. *************************************************************************** 

## **CARD 46description  and 46 .** 

JTRAN_I1,  JTRAN_IM,  JTRAN_K1,  JTRAN_KM 

JTRAN_I1 The boundary layer is treated as laminar on the I=1 blade surface up to this point beyond which the transition criterion based on FTRANS is applied. JTRAN_IM The boundary layer is treated as laminar on the I=IM blade surface up to this point beyond which the transition criterion based on FTRANS is applied. JTRAN_K1 The boundary layer is treated as laminar on the K=1 hub surface up to this point beyond which the transition criterion based on FTRANS is applied. JTRAN_KM The boundary layer is treated as laminar on the K=KM casing surface up to this point beyond which the transition criterion based on FTRANS is applied. 

The J values are measured relative to the start of the current row, not the start of the whole machine. They are automatically changed later to the J values for the whole machine. Set them all = 0 and FTRANS to zero for fully turbulent boundary layers. 

There are no defaults for these values . 

*************************************************************************** 

## **CARD 47description  and 47 .** 

NEW_GRID 

NEW_GRID NEW_GRID is used to decide whether or not to generate a new grid, with different streamwise  (J index)  points, for this blade row.  Set NEW_GRID = 1  to generate a new grid, in which case extra data will be input in the section headed NEW GRID DATA .   Set NEW_GRID = 0  to use the grid points read in as data as the grid for the calculation. 

NEW_GRID  is a very useful way of refining the grid when greater accuracy is required. The number of streamwise (J) points can be increased or they can be clustered in places of interest. 

There is no default for this data . 

*************************************************************************** 

## **CARD 48description  and 48 .** 

RPMROW, RPMHUB 

RPMROW The rotational speed of this blade row, in RPM.  It is positive if the rotation is in the positive tangential direction. RPMHUB The rotational speed of the hub of this blade row, in RPM. Positive if the rotation is in the positive tangential direction. 

Warning the RPM may often be negative. The hub rotation need not be the same as the blade rotation, e,g. a cantilevered compressor stator with a rotating hub. The casing is taken to be rotating at the same speed as the blade row between the limits JROTTS  and JROTTE, input in the next card, elsewhere the casing rotation is zero. 

There are no defaults for these values. 

*************************************************************************** 

## **CARD 49description  and 49 .** 

JROTHS,  JROTHE,  JROTTS,  JROTTE 

JROTHS The J value at which the hub starts rotating at RPMHUB. JROTHE The J value at which the hub stops rotating at RPMHUB . JROTTS The J value at which the casing starts rotating at RPMROW . JROTTE The J value at which the casing stops rotating at RPMROW . 

Beyond these values the rotations are taken to be zero. The J values are relative to the start of this blade row not those for the whole machine. Set both values = JMROW if a stationary hub or casing is required. Note that the J values are those for the grid used in the input data, they are automatically reset if NEW_GRID is used. 

There are no defaults for these values. 

*************************************************************************** 

## **CARD 50description  and 50 .** 

PUPROW,  PLEROW,  PTEROW,  PDNROW 

PUPROW An initial guess of the static pressure at inlet to this blade row. In N/m[2] . PLEROW An initial guess of the static pressure at the leading edge of this blade row. In N/m[2] . PTEROW An initial guess of the static pressure at the trailing edge of this blade row. In N/m[2] . PDNROW An initial guess of the static pressure at the exit to this blade row. In N/m[2] . 

These are only used for the initial guess of the flow field, they should not affect the final solution but the more accurate they are the faster will be the convergence. 

There are no defaults for these values . 

*************************************************************************** 

## **CARD  51description  and 51 .** 

NSECS_ROW, INSURF 

NSECS_ROW The number of quasi-stream surfaces on which the blade sections of this row will be input. This is usually the same as NSECS_IN but if it is different then interpolation in the NSECS_ROW input sections will be used to obtain data on NSECS_IN uniformly spaced sections. 

INSURF 

Determines whether the first and last sections of the NSECS_ROW input sections will be on the hub and casing. Usually set INSURF = 0, so the first section is the hub and the last section the casing. If INSURF = 1 the coordinates of the hub stream surface will be read in later under “Annulus Geometry”. If INSURF = 2 then the coordinates of the casing stream surface will be read in later under “Annulus Geometry”. If INSURF > 2 then the coordinates of both the hub and casing will be read in later under “Annulus Geometry”. 

If a new hub surface geometry is input then the first stream surface used to define the blade geometry should be at a lower radius than the new hub. If a new casing surface geometry is input then the last stream surface used to define the blade geometry should be outside of the new casing. Otherwise extrapolation is necessary, which may be very inaccurate. 

The defaults are  NSECS_ROW = NSECS_IN  and  INSURF = 0 *************************************************************************** 

## **CARD 52description  and 52 .** 

IF_CUSP,  IF_ANGLES 

IF_CUSP Determines whether a cusp will automatically be generated for this blade row. If  IF_CUSP = 0 no cusp will be generated. If  IF_CUSP = 1 a cusp will be generated and extra data will be needed in card 53 . IF_CUSP = 2 the body force model will be used to force trailing edge separation and extra data will be needed in Card 54 . 

IF_ANGLES Determines whether the grid angles upstream and downstream of the blade row are generated by extrapolation from the blade centre line or are read in as data in Cards 66-70. IF_ANGLES = 0 means use extrapolation, IF_ANGLES = 1 means read in the angles in Cards 66-70 . 

Defaults are  IF_CUSP =0 ,  IF_ANGLES = 0 

*************************************************************************** 

## **CARD 53.** 

## **This card is only needed if IF_CUSP in card 52 was = 1 .** 

ICUSP,  LCUSP,  LCUSPUP 

ICUSP The cusp is centred on the blade centre line if ICUSP = 0 . It is flush with the I=1 blade surface if ICUSP = 1  and with the I=IM blade surface if ICUSP = -1.  Usually ICUSP = 0 . LCUSP The number of grid cells on the cusp. Typically LCUSP = 3 . LCUSPUP The cusp is started LCUSPUP grid points upstream of the trailing edge point. Usually LCUSPUP = 0 . 

A trailing edge cusp is usually used for blades with a thick trailing edge as it gives a better representation of the real flow. If one is not used then negative loading is likely to occur near the trailing edge and this is not found in practice. 

The use of a cusp at the trailing edge is described in Note 15. 

There are no defaults for this data. *************************************************************************** 

## **CARD 54 .** 

## **This card only needed if IF_CUSP = 2 so a body force is being used to force separation at  the trailing edge.** 

NUP_I1,  NUP_IM,  NWAKE,  SEP_THIK,   SEP_DRAG 

NUP_I1 The body force starts NUP_I1 points upstream of the trailing edge on the I=1 blade surface. 

NUP_IM The body force starts NUP_IM points upstream of the trailing edge on the I=IM blade surface. N_WAKE The body force extends N_WAKE grid points downstream of the trailing edge. N_WAKE may be negative. 

SEP_THICK The body force is applied to all grid points which are greater than a distance (SEP_THICK x blade thickness at the separation point) from the extrapolated blade surface. Typical value = 0.01. The value can be made negative to increase the pitchwise extent of the body force field. 

SEP_DRAG The magnitude of the body force is proportional to (1-SEP_DRAG). Typical value = 0.99. Reducing this value increases the body force . 

The body force model to force separation at a trailing edge is described in Note 16. 

This option is seldom used. A cusp is generally preferred. 

There are no defaults for this data. 

************************************************************************** 

******************************************************************************* 

***************************************************************************** 

**NEXT START TO INPUT THE DATA ON EACH  OF  THE “NSECS_ROW”  QUASI STREAM SURFACES WHICH ARE USED TO SPECIFY THE BLADE SHAPE.** 

**NOTE THAT IF KM = 2  THEN ONLY A SINGLE STREAM SURFACE MUST BE USED FOR BLADE GEOMETRY INPUT.** 

**RETURN TO THIS POINT AFTER DATA ON ALL BUT THE LAST STREAM SURFACE HAS BEEN INPUT.** 

*************************************************************************** ************************************************************************** 

## **CARD 55 .** 

BLANK CARD This is just used to space out the data set. *************************************************************************** 

## **CARD 56 .** 

BLANK CARD This is just used to space out the data set. *************************************************************************** 

## **CARD 57 .** 

IF_DESIGN,  IF_RESTAGGER,  IF_LEAN 

IF_DESIGN = 0 If there are no changes to this blade section. 

= 1 If this section is to be redesigned using data from the cards entitled “Blade Redesign Data” at the end of the main data description in which case the usual data input on the stream surface, Cards  58 to  65,  are not used. 

IF_RESTAGGER = 0 If this blade section is not rotated. = 1 to rotate this section using the data in Card 65A . 

IF_LEAN = 0 If this section is not leaned. = 1 to lean this section using the data in Card 65B . 

Defaults are:  IF_DESIGN = 0 , IF_RESTAGGER = 0,  IF_LEAN = 0. 

**Jump to the section entitled  “Blade Design Data”   if   IF_DESIGN is not zero. Cards 58  to 65 are then not needed for this stream surface.** 

*************************************************************************** 

## CARD 58 . 

FAC1,  XSHIFT 

FAC1 The axial coordinates input in the next card are scaled by FAC1. Usually = 1.0 but may use 0.001 if the coordinates are input in millimeters, since the final coordinates must be in metres. 

XSHIFT The axial coordinates input in the next card are shifted a distance XSHIFT in the axial direction. XSHIFT is applied before scaling by FAC1 and so should be in the same units as XSURF . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 59 .** 

XSURF(J,K),  J = 1, JMROW 

XSURF XSURF are the axial coordinates of the points on the stream surface used to define the blade shape. The values are scaled by FAC1 so that the final coordinates are in metres. Note that this must include points upstream and downstream of the blade as well as on it. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 60 .** 

FAC2,  TSHIFT 

FAC2 The r-theta coordinates input in the next card are scaled by FAC2. Usually = 1.0 but may use 0.001 if the coordinates are input in millimeters, since the final coordinates must be in metres. TSHIFT The r-theta coordinates input in the next card are shifted a distance TSHIFT in the circumferential direction. TSHIFT is applied before scaling by FAC2 and so should be in the same units as RT_UPP . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 61 .** 

RT_UPP(J,K),  J = 1,JMROW 

RT_UPP 

RT_UPP are the r-theta coordinates of the points on the upper surface of the blade on the stream surface used to define the blade shape. The upper surface is the one with the largest r-theta coordinate and for which the “I” index is 1. The values are scaled by FAC2 so that the final coordinates are in metres. Note that this must include points upstream and downstream of the blade as well as on it. The points upstream and downstream of the blade should be roughly aligned with the relative flow. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 62** 

FAC3 

FAC3 

The blade tangential thickness , delta(r-theta) , input in the next card is scaled by FAC3. Usually = 1.0 but may use 0.001  if the coordinates are input in millimeters, since the final coordinates must be in metres. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 63 .** 

RT_THICK(J,K),  J = 1,JMROW 

RT_THICK 

RT_THICK is the blade tangential thickness, delta(r-theta) at the points on the stream surface used to define the blade shape. The values are scaled by FAC3 so that the final coordinates are in metres. Note that this must include points upstream and downstream of the blade, where the tangential thickness will be zero, as well as on the blade. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 64 .** 

FAC4,  RSHIFT 

FAC4 The radial coordinates input in the next card are scaled by FAC4. Usually = 1.0 but may use 0.001 if the coordinates are input in millimeters, since the final coordinates must be in metres. RSHIFT The radial coordinates input in the next card are shifted by RSHIFT before being used. . RSHIFT is applied before scaling by FAC4 and so should be in the same units as RSURF . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 65 .** 

RSURF(J,K),  J = 1,JMROW 

RSURF RSURF is the radius, of the points on the stream surface used to define the blade shape. The values are scaled by FAC4 so that the final coordinates are in metres. Note that this must include points upstream and downstream of the blade. The points upstream and downstream of the blade should be roughly aligned with the flow, i.e. with the meridional streamlines. 

There are no defaults for this data. 

*************************************************************************** 

*************************************************************************** *************************************************************************** 

**If  IF_DESIGN is not = zero then insert here the cards from the section entitled  “BLADE REDESIGN DATA”  which is at the end of the main input data.  If    IF_DESIGN  is equal to zero continue with Card 65A .** *************************************************************************** *************************************************************************** 

If  IF_RESTAGGER  in Card  57 was not zero then insert the following card to restagger the blade section 

## **CARD 65Adescription  and 65A** 

ROTATE. FRACX_ROT 

ROTATE The angle of clockwise rotation of the blade section, in degrees. FRACX_ROT The centre of rotation as a fraction of the axial chord. Usually = 0.5 

Note that this option changes all the local blade angles on the stream surface by ROTATE degrees whilst keeping the stream surface geometry unchanged. It can be used for both axial and radial flow machines 

Defaults are ROTATE = 0.0  and FRACX_ROT = 0.5. 

*************************************************************************** 

If  IF_LEAN in Card  57 was not zero then insert the following card to lean the blade. 

## **CARD 65Bdescription  and 65B** 

ANGLEAN 

ANGLEAN The angle by which this blade section is leaned relative to the first section. In degrees. Positive if the lean is in the positive circumferential (i.e. theta) direction. 

Default is ANGLEAN = 0.0 

*************************************************************************** 

*************************************************************************** *************************************************************************** 

**If KM = 2 so that a quasi-three dimensional blade-to-blade calculation is being performed then insert here the cards from the section at the end of the main data input entitled  “QUASI-3D DATA” .** 

## **If KM is greater than 2 continue with the main data set, CARD 66 .** 

*************************************************************************** *************************************************************************** 

*************************************************************************** ************************************************************************* END OF BLADE GEOMETRY INPUT ON ONE QUASI STREAM SURFACE.** 

## **RETURN TO CARD   55   FOR THE NEXT QUASI STREAM SURFACE UNLESS THIS WAS THE LAST ONE.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

**If  INSURF is not = zero then insert here the cards which define the hub and casing geometry which are described at the end of the main input data under the heading    “ANNULUS GEOMETRY DATA”.** 

**If  INSURF  is equal to zero continue with Card 66 .** 

*************************************************************************** *************************************************************************** 

## **CARDS 66  to 70 are only needed if   IF_ANGLES(NR)  for this blade row was greater than zero.** 

## **CARD 66description and 66** 

N_ANGLES 

N_ANGLES The number of spanwise positions at which the grid angles upstream and downstream of the blade row will be specified. Usually 3 to 5 points are sufficient. 

## **CARD 67** 

FRACN_SPAN(N), N=1,N_ANGLES 

FRACN_SPAN The fraction of blade span at which the grid angles will be specified. 

## **CARD 68** 

ANGL_UP(N), N=1,N_ANGLES 

ANGL_UP the grid angles upstream of the blade row at the above fractions of span. In degrees. Positive if flow along the grid angle would have a positive tangential velocity. 

## **CARD 69** 

ANGL_DWN1(N), N=1,N_ANGLES 

ANGL_DNW1 the grid angles downstream of the blade row at the blade trailing edge at the above fractions of span. In degrees. Positive if flow along the grid angle would have a positive tangential velocity. 

## **CARD 70** 

ANGL_DWN2(N), N=1,N_ANGLES 

ANGL_DWN2 the grid angles downstream of the blade row at the last grid point in the row, usually the mixing plane or downstream boundary, at the above fractions of span. In degrees. Positive if flow along the grid angle would have a positive tangential velocity. 

There are no defaults for this data 

*************************************************************************** 

## **CARDS TF1  to TF3  are only needed if IM = 2 so that a throughflow calculation is being performed.** 

## **CARD TF1description  and TF1** 

ANGL_TYP, NANGLES 

ANGL_TYP If  ANGL_TYPE = “A” The blade exit flow angle is specified directly in CARD TF3. If ANGL_TYP = “D” it is specified as a deviation angle from the blade centre line. 

NANGLES The exit flow angles are specified at NANGLES spanwise positions. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD TF2** 

FRAC_SPAN(N), N= 1,NANGLES 

FRAC_SPAN The fraction of span at which the angles will be given. NANGLE values must be input. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD TF3** 

EXIT_ANGL(N), N=1,NANGLES 

EXIT_ANGL The blade exit flow angle or deviation angle depending on ANGL_TYP . In degrees. Flow angles are positive if flow along that angle would have a positive tangential velocity. Deviation angles are measured from the blade centre line angle and are positive if the flow departs from that angle in a clockwise direction. 

There are no defaults for this data. 

*************************************************************************** 

*************************************************************************** *************************************************************************** 

**If  NEW_GRID is not = zero then insert here the cards which define the new number and new positions of the streamwise (J) grid points as described at the end of the main input data under the heading “NEW GRID DATA” .  If  NEW_GRID  is equal to zero continue with Card 71 .** 

*************************************************************************** *************************************************************************** 

*************************************************************************** 

*************************************************************************** 

## **END OF ALL DATA INPUT ON ONE BLADE ROW. RETURN TO CARD   38   TO START ON THE NEXT BLADE ROW UNLESS THIS WAS THE LAST ROW.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** 

**AFTER INPUTTING THE BLADE GEOMTRY ON ALL STREAMWISE SURFACES START TO INPUT DATA FOR THE INLET AND EXIT BOUNDARY CONDITIONS.** *************************************************************************** 

## **CARD 71 .** 

BLANK CARD 

This is only used to space out the data. It must be input. 

*************************************************************************** 

## **CARD 72 .** 

BLANK CARD 

This is only used to space out the data. It must be input. 

*************************************************************************** 

## **CARD 73 .** 

KIN 

KIN 

KIN is the number of points at which the inlet boundary conditions and the exit static pressure profile will be input in the next set of cards. 

There is no default for this data. 

*************************************************************************** 

## **CARD 74description  and  74 .** 

FR_IN(K), K = 1, KIN-1 

FR_IN(K) FR_IN is a table of the relative spanwise grid spacings of the points where the boundary conditions are given. Only the relative spacing are needed the absolute values do not matter. If FR_IN(3)  is set to zero then the spacings are generated automatically as a geometric progression with expansion ratio FR_IN(1)  and maximum spacing ratio = FR_IN(2) . These are applied away from both endwalls . Typical values are FR_IN(1) = 1.25, FR_IN(2) = 10.0, FR_IN(3) = 0.0  .  All the remaining  KIN-4 values must still be input but they are not used. 

Note there are KIN-1 spacings for the KIN points. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  75description  and 75.** 

PO1(K), K = 1, KIN 

PO1(K) PO1 is the inlet stagnation pressure at points on the inlet boundary spaced by FR_IN . In N/m[2] . The first point must be on the hub and the last point on the casing . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  76description and 76 .** 

## **This card is only needed if IPOUT = 3** 

PD(K), K = 1,KIN 

PD(K) PD is the exit static pressure at points on the outlet boundary spaced by FR_IN . In N/m[2] . The first point must be on the hub and the last point on the casing . 

This data is only needed if  IPOUT = 3, otherwise the exit pressure is fixed by other methods. See note 2 for more details on the use of IPOUT. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  77description  and 77 .** 

IF IFGAS = 0  or  IFGAS = 1 then READ TO1(K), K = 1,KIN 

IF  IFGAS = 3, then READ HOIN(K), K=1,KIN 

TO1(K) If IFGAS = 0 or 1 then TO1 is the inlet absolute stagnation temperature at points on the inlet boundary spaced by FR_IN . In degrees K . The first point must be on the hub and the last point on the casing . 

HOIN(K) If IFGAS = 3 then HOIN is the inlet stagnation enthalpy in kJ/kg. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  78description  and 78 .** 

VTIN(K), K = 1,KIN 

VTIN(K) VTIN is the inlet absolute tangential velocity at points on the inlet  boundary spaced by FR_IN . In m/sec . The first point must be on the hub and the last point on the casing . 

Note that the value of VTIN is only used as an initial guess if  IN_VTAN = 0  or = 2. It is the fixed value of inlet absolute tangential velocity if  IN_VTAN = 1 . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  79description  and 79 .** 

VM1(K), K = 1,KIN 

VM1(K) 

VM1 is an initial guess of the inlet meridional velocity at points on the inlet boundary spaced by FR_IN . In m/sec . The first point must be on the hub and the last point on the casing . 

This is only an initial guess but it determines the initial mass flow rate and so should be as accurate as possible. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  80description  and 80 .** 

BS(K), K = 1,KIN 

BS(K) BS is the inlet yaw angle based on the meridional velocity, i.e. tan[-1] (Vθ/Vm) at points on the inlet boundary spaced by FR_IN . In degrees. It is positive if the tangential velocity is positive. The first point must be on the hub and the last point on the casing . 

Note that this is the absolute angle if IN_VTAN = 0 and the relative angle if IN_VTAN = 2. It is not used if IN_VTAN = 1 but must still be input. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD  81description  and 81 .** 

BR(K), K = 1,KIN 

BR (K) BR is the inlet pitch angle i.e. tan[-1] (Vr/Vx) at points on the inlet boundary spaced by FR_IN . In degrees. The first point must be on the hub and the last point on the casing . 

BR is the fixed meridional pitch angle at inlet if IN_VR = 1 . It is not used for the other options of IN_VR but values must still be input. 

There are no defaults for this data. 

*************************************************************************** 

## **CARD 82description  and 82 .** 

PDOWN_HUB,  PDOWN_TIP 

PDOWN_HUB The exit static pressure on the hub. In N/m[2] . This is always used for the initial guess but is only used during the calculation if  IPOUT = 0 or 1 . 

PDOWN_TIP The exit static pressure on the casing. In N/m[2] . This is always used for the initial guess but it is only used during the calculation if  IPOUT =  1  or  -1. 

This is the main exit boundary condition. Accurate values should be input even when they are only used for the initial guess. See Note 2 for details of how IPOUT is used. 

There is no default for this data. 

*************************************************************************** 

## **CARD 83description  and 83 .** 

## **Only needed if  ILOS = 10, to use the original mixing length model.** 

For each of  NROWS blade rows input, 

XLLIM_I1, XLLIM_IM, XLLIM_K1,XLLIM_KM, XLLIM_DWN, XLLIM_UP 

XLLIM_I1 The mixing length limit on the blade lower (I=1) surface as a fraction of the blade pitch. Typical value = 0.03 . 

XLLIM_IM The mixing length limit on the blade upper (I=IM) surface as a fraction of the blade pitch. Typical value = 0.03 . 

XLLIM_K1 The mixing length limit on the hub (K=1) as a fraction of the mid-span blade pitch. Typical value = 0.03 . 

XLLIM_KM The mixing length limit on the casing, K=KM, as a fraction of the mid-span blade pitch. Typical value = 0.03 . 

XLLIM_DWN The mixing length limit on streamwise (K=constant) surfaces downstream of the trailing edge of the blade row as a fraction of the blade pitch. Typical value = 0.04 . 

XLLIM_UP The mixing length limit on the streamwise (K=constant) surfaces upstream of the leading edge of the blade row as a fraction of the blade pitch. Typical value = 0.02 . 

There are NROWS lines of data needed here.  Increase the mixing length limits if the flow is known to be highly turbulent or in regions where separations occur. 

The defaults are that all mixing length limits = 0.03, except XLLIM_UP = 0.02. *************************************************************************** 

## **CARD 84description  and 84 .** 

## **Only needed if ILOS = 100 or = 200 so that the loss routines NEWLOSS or SPAL_LOSS are being used.** 

XLLIM_IN,  XLLIM_LE,  XLLIM_TE,  XLLIM_DN, FSTURB, TURBVIS_DAMP 

For each of NROWS blade rows input 

XLLIM_IN The mixing length limit at the upstream boundary to the blade row. Typical value = 0.02 . 

XLLIM_LE The mixing length limit at the leading edge of the blade row. Typical value = 0.03 . XLLIM_TE The mixing length limit at the trailing edge of the blade row. Typical value = 0.04 . XLLIM_DN The mixing length limit at the exit boundary of the blade row. Typical value = 0.05 . 

FSTURB The free stream turbulent viscosity as a multiple of the laminar viscosity. Usually = 0.0 but increase in regions of high turbulence. 

TURBVIS_DAMP On passing through a mixing plane the turbulent viscosity downstream of the plane is this multiple of the pitchwise averaged turbulent viscosity upstream of the mixing plane. Typical value = 0.5, but this is very much a guess. 

There are NROWS lines of data needed here.  Increase the mixing length limits and  FSTURB if the flow is known to be highly turbulent or in regions where separations occur. 

The defaults are XLLIM_IN = 0.02, XLLIM_LE = 0.03, XLLIM_TE = 0.04, XLLIM_DN = 0.05,  FSTURB = 1.0, TURBVIS_DAMP = 0.5 . 

*************************************************************************** 

## **CARD 85description  and 85 .** 

FACMIXUP, NMIXUP 

FACMIXUP The mixing length limits input above are increased by this factor for the first NMIXUP time steps. This helps to overcome initial transients. Typical value = 2.0 . NMIXUP The mixing length limits are decreased from (FACMIXUP x the input values)  to the input values over the first NMIXUP time steps.  Typical value NMIXUP = 1000 . 

This applies to all turbulence models. It is not usually necessary to increase the turbulent viscosity and may slow convergence slightly so set FACMIXUP to zero if not required. The increase in mixing lengths is not used if starting from a restart file. 

The defaults are FACMIXUP = 2.0, NMIXUP = 1000. *************************************************************************** 

## **CARD 86description  and 86 .** 

## **This card only needed if  IF_ROUGH  in Card 20  is greater than zero .** 

For each of NROWS blade rows input 

ROUGH_H,  ROUGH_T,  ROUGH_L,  ROUGH_U 

ROUGH_H Is the surface roughness on the hub, in microns. ROUGH_T Is the surface roughness on the casing, in microns. ROUGH_L Is the surface roughness on the passage lower, I = 1, surface,  in microns. ROUGH_U Is the surface roughness on the passage upper. I= IM, surface, in microns. 

There are NROWS of values needed. Note that the passage lower surface is the blade upper surface, I = 1,  and vice versa. 

The defaults are that all surfaces are hydraulically smooth, with zero roughness. *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **If IFCOOL is not zero then input here the cards used to define the cooling flows.  These are described near the end of the data input.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **If IFBLEED is not zero then input here the cards used to define the bleed flows.  These are described near the end of the data input.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **If there is shroud leakage on any blade row, as defined by KTIPS being set to less than zero,  then input here the cards used to define the shroud leakage flows.  These are described near the end of the data input.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **END OF ALL DATA INPUT** 

*************************************************************************** *************************************************************************** 

## BLADE REDESIGN DATA 

*************************************************************************** 

******************************************************************** 

**The following cards number IFDES1 to IFDES4  are input if using the blade section redesign option.  These are needed for every blade section for which IF_DESIGN was non-zero.** 

*************************************************************************** *************************************************************************** 

## **CARD IFDES1description and IFDES1** 

N_SS,  N_LE,  N_TE 

N_SS The number of points used to define the new stream surface.  Typically about 8 points are sufficient. N_LE The number of the leading edge point in the N_SS input points. N_TE The number of the trailing edge point in the N_SS input points. 

Note that there must be an input point at the leading edge and one at the trailing edge. 

*************************************************************************** 

## **CARD IFDES2description and IFDES2** 

For N = 1, N_SS ,     i.e. N_SS lines of data in total  . Input XSS(N), RSS(N), RELSPACE(N) 

XSS The axial coordinate of the point on the stream surface. In metres. RSS The radius of the point on the stream surface. In metres. RELSPACE The relative grid spacing of the final grid points at the point on the stream surface. Only the relative values are needed the absolute values are not used. 

Note. Interpolation between the points is used so that the input points must define a smooth surface and the spacing of the points should note change suddenly. 

The stream surface shape is set by this redesign procedure, not by the usual stream surface data input. 

************************************************************************** 

## **CARD IFDES3description and IFDES3 .** 

NNEW, NSMOOTH 

NNEW The number of points at which new blade geometry will be input in the next card. Typically 5 to 10 points are sufficient. 

NSMOOTH The number of times that the new blade data will be smoothed.  Typical value = 2 . 

There are no defaults for this data . ************************************************************************** 

## **CARD  IFDES4description and IFDES4 .** 

For N = 1 to NNEW input the following data, i.e. NNEW cards in total. FRACNEW(N) ,BETANEW(N), THICKUP(N), THICKLOW(N) 

FRACNEW The fraction of meridional chord at which the blade details are given. The first value must be 0.0  and the last value = 1.0 BETANEW The blade camber line angle at FRACNEW. In degrees. It is positive if a vector in the direction of the angle would have a positive tangential component. THICKUP The blade tangential thickness above the camber line as a fraction of the axial chord. THICKLOW The blade tangential thickness below the camber line as a fraction of the axial chord. 

If THICKUP is not equal to THICKLOW then the camber line is not a true centre line of the blade. 

There are no defaults for this data. 

************************************************************************** 

## **CARD IFDES5description and IFDES5** 

FRAC_CHORD_UP,  FRAC_CHORD_DWN,  RTHETA_MID 

FRAC_CHORD_UP The grid extension upstream of the leading edge as a fraction of the meridional chord. 

FRAC_CHORD_DWN The grid extension downstream of the trailing edge as a fraction of the meridional chord. 

RTHETA_MID The tangential coordinate of the mid grid point, i.e. the point with the mid  J  value.. This may be used to change the blade stacking but is usually set it = 0.0 

There are no defaults for this data 

************************************************************************** 

************************************************************************** ************************************************************************** 

## **End of data input for the redesign option. Return to the main input data, Card 66.** 

************************************************************************** ************************************************************************** 

## **DATA FOR A QUASI-3D BLADE-TO-BLADE CALCULATION** 

**This data is only input when KM=2.** 

## **CARD Q3D1description and Q3D1** 

Q3DFORCE,  TKSS_REF 

Q3DFORCE A factor scaling the force which is applied to keep the flow on the specified stream surface. Typical value = 1.0 but larger values are often stable and will give faster convergence. TKSS_REF The stream tube thickness at the first grid point as a fraction of the blade chord. Previously this was hard coded at 0.05 but it has sometimes been found necessary to use a lower value. 0.02 is typical. This is only available in version 20.6. **CARD Q3D2** NSS NSS The number of points used to define the stream surface, usually about 5 points should be sufficient **CARD Q3D3** FRACSS(N), N=1,NSS NSS values of the fraction of distance along the stream surface at which its thickness will be given. The distance is measured from the first point on the input stream surface and its length is the meridional distance from the first to last points on the input stream surface. Hence FRACSS(1) = 0.0  and FRACSS(NSS) = 1.0 . **CARD Q3D4** 

TKSS(N), N=1,NSS The relative stream surface thickness at points FRACSS. The relative thickness is the local value divided by the value at the first point. 

There are no defaults for this data. 

Note that only a single stream surface must be used to define the geometry if KM = 2 . 

See Note 19 for more details of the Q3D model. 

**End of Q3D data return to main data input, Card 66 ********************************************************** 

## **ANNULUS GEOMETRY DATA** 

************************************************************************ ****************************************************************** 

**Cards to define a new annulus geometry which are needed for any blade row for which  INSURF is greater than zero.** 

************************************************************************** ************************************************************************** 

## **CARD  INSRF1 .** 

## **This card only needed if INSURF = 1  or INSURF > 2 .** 

NHUB 

NHUB NHUB is the number of points which will be used to define the hub stream surface if INSURF = 1  or INSURF > 2 . Typically use about 5 points per blade row. 

There are no defaults for this data. 

************************************************************************** 

## **CARD INSRF2 .** 

## **This card only needed if INSURF = 1  or INSURF > 2 .** 

XHUB(N), N=1 to NHUB.   i.e. NHUB values in total . 

XHUB Axial coordinates of points on the hub stream surface. They are scaled by FAC1 so that the final coordinates are in metres. 

There should be several points per blade row so that the hub stream surface is well defined. There are no defaults for this data. 

************************************************************************** 

## **CARD INSRF3 RHUB(N) ,  N=1,NHUB** 

## **This card only needed if INSURF = 1  or INSURF > 2 .** 

RHUB(N), N=1 to NHUB.   i.e. NHUB values in total . 

RHUB Radial coordinates of points on the hub stream surface. They are scaled by FAC4 so that the final coordinates are in metres. 

There should be several points per blade row so that the hub stream surface is well defined. 

There are no defaults for this data. 

************************************************************************** 

## **CARD INSURF4 .** 

## **This card only needed if INSURF = 2  or INSURF > 2 .** 

NTIP 

NTIP NTIP is the number of points which will be used to define the casing stream surface if INSURF = 2  or INSURF > 2 . Typically use about 5 points per blade row. 

There are no defaults for this data. 

************************************************************************** 

## **CARD INSRF5 .** 

## **This card only needed if INSURF = 2  or INSURF > 2 .** 

XTIP(N),  N = 1 to NTIP.  i.e.  NTIP values in total. 

XTIP Axial coordinates of points on the casing stream surface. They are scaled by FAC1 so that the final coordinates are in metres. 

There should be several points per blade row so that the casing stream surface is well defined. 

There are no defaults for this data. 

************************************************************************** 

## **CARD INSRF6 .** 

## **This card only needed if INSURF = 2  or INSURF > 2 .** 

RTIP(N),  N=1 to NTIP .  i.e. NTIP values in total. 

RTIIP Radial coordinates of points on the casing stream surface. They are scaled by FAC4 so that the final coordinates are in metres. 

There should be several points per blade row so that the casing stream surface is well defined. There are no defaults for this data. 

************************************************************************** ************************************************************************** 

**End of data input to define new hub and casing geometry.  Return to the main data input CARD 66.** 

************************************************************************** 

## **NEWGRID  DATA** 

****************************************************************** ****************************************************************** 

**The following Cards  NG_1  to NG_12  are only needed if subroutine NEWGRID  is used to generate a new grid with a different number of streamwise (J index) grid points This is done for any blade row for which NEW_GRID is greater than zero.** 

******************************************************************** 

******************************************************************** 

## **CARD NG_1 .** 

BLANK CARD This is just used to space out the data. 

*************************************************************************** 

## **CARD NG_2 .** 

NUP, NON, NDOWN 

NUP NUP is the number of grid points upstream of the leading edge to be generated by subroutine NEWGRID. 

NON NON is the number of grid points on the blade surface to be generated by subroutine NEWGRID . 

NDOWN NDOWN is the number of grid points downstream of the trailing edge to be generated by subroutine NEWGRID . 

Subroutine NEWGRID will generate a new grid with this number of points. If any of  NUP, NON  or NDOWN are zero  the grid point spacing are generated from a table of a few relative grid point spacings as in Card NG_4.  If NUP, NON or NDOWN are greater than zero then the relevant grid spacings, i.e.  upstream, on or downstream of the blade, are read in from a table of spacing as in Card NG_5.  The second option is the most usual . 

There are no defaults for this data. 

*************************************************************************** 

## **CARD NG_3 .** 

## **This is only needed if NUP from the last card, NG_2, was zero.** 

NUP 

NUP 

NUP is the number of grid points upstream of the leading edge to be input in the next card. This new value of NUP overwrites the value of zero set in CARD NG_2. 

*************************************************************************** 

## **CARD NG_4 .** 

## **This is only needed if NUP in card NG_2 was zero .** 

XFRACUP(N) , RELSPUP(N) , N=1,NUP 

XFRACUP(N) A table of fractional distances upstream of the blade leading edge at which the grid spacing will be given. The first value must be 0.0  and the last value must be 1.0 . 

RELSPUP(N) The relative grid spacing at XFRACUP(N) . 

Note only the relative spacings are needed, the absolute value do not matter. The advantage of the type of input compared to that in Card NG_5 is that far fewer points need to be given, typically 4 or 5 points will suffice. 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_5 .** 

## **This is only needed if NUP in card NG_2 was greater than zero .** 

UPF(J) J = 1,NUP 

UPF(J) NUP values of the relative grid spacing upstream of the leading edge of the blade row.  Only the relative spacing are needed, the absolute values do not matter. 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_6 .** 

## **This is only needed if  NON  in card  NG_2 was zero.** 

NON 

NON 

NON is the number of grid points on the blade surface to input in the next card. This new value of NON overwrites the value of zero set in Card NG_2 . 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_7 .** 

## **This is only needed if NON in card NG_2 was zero .** 

XFRACON(N) , RELSPON(N) , N = 1,NON 

XFRACON(N)  A table of fractional distances ON the blade surface at which the grid spacing will be given. The first value must be 0.0  and the last value must be 1.0 . RELSPON(N) The relative grid spacing at XFRACON(N) . 

Note only the relative spacings are needed the absolute value do not matter. The advantage of the type of input compared to that in Card NG_8 is that far fewer points need to be given, typically 4 or 5 points will suffice. 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_8 .** 

## **This is only needed if NON in card NG_2 was greater than zero .** 

ONF(J) J = 1,NON 

ONF(J) NON values of the relative grid spacing on the blade surface.  Only the relative spacing are needed the absolute values do not matter. 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_9 .** 

## **This is only needed if NDOWN from card  NG_2 was zero.** 

NDOWN 

NDOWN NDOWN is the number of grid points downstream of the trailing edge to be input in the next card. This new value of NDOWN overwrites the value of zero set in Card NG_2 . 

There is no default for this data. 

## **CARD NG_10 .** 

## **This is only needed if  NDOWN in card NG2 was zero .** 

## XFRACDWN(N) , RELSPDWN(N), N=1,NDOWN 

XFRACDWNP(N) A table of fractional distances downstream of the blade trailing edge at which the grid spacing will be given. The first value must be 0.0  and the last value must be 1.0 . 

RELSPDWN(N) The relative grid spacing at XFRACDWN(N) . 

Note only the relative spacings are needed the absolute value do not matter. The advantage of the type of input compared to that in Card NG_11 is that far fewer points need to be given, typically 4 or 5 points will suffice. 

There is no default for this data. 

*************************************************************************** 

## **CARD NG_11 .** 

## **This is only needed if  NDOWN in card NG2  was greater than zero .** 

DOWNF(J) J = 1,NDOWN 

DOWNF(J) NDOWN values of the relative grid spacing downstream of the blade trailing edge.  Only the relative spacing are needed the absolute values do not matter. 

There is no default for this data. 

*************************************************************************** 

**CARD NG_12 .** 

UPEXT, DWNEXT 

UPEXT 

The upstream extent of the original grid upstream of the leading edge is multiplied by UPEXT. The leading edge position is unchanged. 

DWNEXT 

The downstream extent of the original grid downstream of the trailing edge is multiplied by DWNEXT. The trailing edge point is unchanged. 

Note that if there is another blade row upstream/downstream of the current one and the option to generate the grid between rows automatically using  ISHIFT = 2, 3  or 4 ,  is used, then these numbers will not have any effect. Set UPEXT and DWNEXT both =  1.0  to keep the original grid extensions. 

There are no defaults for this data. 

*************************************************************************** 

*************************************************************************** *************************************************************************** 

## **End of NEWGRID data for the current blade row. Return to the main data input, CARD 71.** 

*************************************************************************** *************************************************************************** 

## **COOLING FLOW DATA** 

*************************************************************************** *************************************************************************** 

**If IFCOOL is not zero insert here the cards which define the cooling flows for each blade row. The data is the same for IFCOOL = 1  or IFCOOL = 2. Note that the option IFCOOL= 2 is only included in version 18.3  and above.** 

*************************************************************************** *************************************************************************** *************************************************************************** *************************************************************************** 

## **For N = 1 to NROWS  insert the following cards.** 

*************************************************************************** *************************************************************************** 

## **CARD    CWL1description   and CWL1 .** 

NCWLBLADE,  NCWLWALL 

NCWLBLADE The number of cooling flow patches on the blade surfaces. 

NCWLWALL The number of cooling flow patches on the hub and casing. 

Set these to zero if there is no cooling on this blade row. ************************************************************************** 

## **FOR N =1, NCWLBLADE  input CARDS   CWL2 and CWL3** 

## **CARD     CWL2description  and CWL2 .** 

IC,  JCBS,  JCBE,  KCBS, KCBE 

IC The “I” value of the blade surface through which coolant is being ejected. Must = 1  or  IM . 

JCBS The “J” value at the start of the cooling patch. JCBE The “J” value at the end of the cooling patch. KCBS The “K” value at the start of the cooling patch. KCBE The “K” value at the end of the cooling patch. 

************************************************************************** 

## **CARD CWL3 .** 

CFLOWB, TOCOOLB, POCOOLB, MACHCOOL, SANGLEB, XANGLEB, RVTIN_B, RPM_COOL 

|CFLOWB|= the mass flow rate of coolant through the current patch|
|---|---|
||for the whole blade row. In Kg/sec.|
|TOCOOLB|= the**absolute**stagnation temperature at which the|
||coolant is supplied to the blade row. In K.|
|POCOOLB|= the**absolute**stagnation pressure at which the|
||coolant is supplied to the blade row. In N/m2.|
||It is only used to estimate the efficiency if IFCOOL = 1.|
||It is used together with the local static pressure to|
||determine the coolant  ejection velocity if IFCOOL = 2.|
|MACHCOOL|= the**relative**Mach number at which the coolant|
||leaves the blade surface. It is used to obtain the coolant|
||ejection velocity if IFCOOL =1.|
||It is not used if IFCOOL = 2.|
|SANGLEB|= the angle between the coolant jet and the plane|
||which is locally tangent to the blade surface. In|
||degrees. See Note 14.|
|XANGLEB|= the angle between the projection of the cooling jet|
||onto the blade surface and a line which is the intersection|
||of the blade surface with a surface  of constant radius, i.e.|
||with a cylindrical surface.  In degrees.  See Note  14 .|
|RVT_IN|Is the angular momentum (radius x tangential|
||velocity) with which the coolant flow is supplied to the|
||blade row by any pre-swirl system. Set = zero if no pre-|
||swirl system.|
|RPM_COOL|Is the rotational speed , in RPM, of the disc  through which|
||the coolant flow is supplied to the blade row. RVT_IN|
||and RPM_COOL  are used to find the pumping work on|
||the coolant between its supply condition to the disc and|
||the point where it enters the mainstream.  Set = zero|
||except for coolant which is supplied to a rotating blade|
||row or disc.|



Note. All this data must be input for each of NCWLBLADE cooling patches on the current blade row. Omit this data if  NCWLBLADE = zero. 

Note that the option IFCOOL = 2 is only available in version 18.3 and above. 

## **Return to Card  CWL2 to insert data for the next blade surface coolant patch on this row.** 

*************************************************************************** 

## **FOR N =1, NCWLWALL  input  CARDS   CWL4  and CWL5** 

## **CARD     CWL4description  and CWL4 .** 

|KC,|JCWS,  JCWE,|ICWS, ICWE|
|---|---|---|
||KC|The “K” value of the endwall surface through which|
|||coolant is being ejected. Must = 1  or  KM .|
||JCWS|The “J” value at the start of the cooling patch.|
||JCWE|The “J” value at the end of the cooling patch.|
||ICWS|The “I” value at the start of the cooling patch.|
||ICWE|The “I” value at the end of the cooling patch.|



*************************************************************************** 

## **CARD  CWL5 .** 

CFLOWW, TOCOOLW, POCOOLW, MACHCOOL, SANGLEW, TANGLEW, RVTIN_W, RPM_COOL 

CFLOWW = the mass flow rate of coolant through the current patch for the whole blade row. In Kg/sec. TOCOOLW = the **absolute** stagnation temperature at which the coolant is supplied to the blade row. In K. POCOOLW = the **absolute** stagnation pressure at which the coolant is supplied to the blade row. In N/m[2] . It is only used to estimate the efficiency if IFCOOL = 1. It is used together with the local static pressure to determine the coolant  ejection velocity if IFCOOL = 2. MACHCOOL = the **relative** Mach number at which the coolant leaves the blade surface. It is used to obtain the coolant ejection velocity if IFCOOL =1. It is not used if IFCOOL = 2. SANGLEW = the angle between the coolant jet and the plane which is locally tangent to the endwall surface. In degrees. See Note 14. XANGLEW = the angle between the projection of the cooling jet onto the endwall surface and a line which is the intersection of the blade surface with a surface of constant circumferential coordinate, i.e. with the axial-radial plane θ = constant. In degrees.  See Note  14. RVTIN_W Is the angular momentum (radius x tangential velocity) with which the coolant flow is supplied to the blade row by any pre-swirl system. Set = zero if no preswirl system. RPM_COOL Is the rotational speed , in RPM, of the disc  through which the coolant flow is supplied to the blade row. RVT_IN and RPM_COOL  are used to find the pumping work on the coolant between its supply condition to the disc and the point where it enters the mainstream.  Set = zero except for coolant which is supplied to a rotating blade row or disc. 

Note. All this data must be input for each of NCWLWALL cooling patches. Omit this data if NCWLWALL = zero. 

Note that the option IFCOOL = 2 is only available in version 18.3 and above. 

## ***************************************************************************** *************************************************************************** Return to Card  CWL4 to insert data for the next endwall surface coolant patch on this row.** 

*************************************************************************** *************************************************************************** *************************************************************************** *************************************************************************** 

## **Return to Card CWL1 to insert cooling flow data for the next blade row.** 

*************************************************************************** *************************************************************************** 

*************************************************************************** *************************************************************************** 

## **End of all data input for cooling flows.  Return to the main data input.** 

*************************************************************************** *************************************************************************** 

## **BLEED FLOW DATA** 

*************************************************************************** *************************************************************************** 

## **If  IFBLEED  is not zero insert here the cards which define the bleed flows for each blade row.** 

*************************************************************************** *************************************************************************** 

## **FOR N = 1, NROWS insert the following cards.** 

## **CARD  BL1description  and BLD1 .** 

NBLEED 

NBLEED The number of bleed patches in this blade row, including both blade surfaces and endwalls. 

********************************************************************* 

## **For N = 1 to NBLEED insert cards BLD2** 

## **CARD BLD2** 

IBLDS, IBLDE, JBLDS, JBLDE, KBLDS, KBLDE, MASSBLED 

IBLDS = the I value where the bleed starts. IBLDE = the I value where the bleed ends. JBLDS = the J value where the bleed starts, defined relative to the start of the current blade row. JBLDE = the J value where the bleed ends, defined relative to the start of the current blade row. KBLDS = the K value where the bleed starts. KBLDE = the K value where the bleed ends. MASSBLED = the mass flow bled off in Kg/s. 

Note that there can be bleed flows through either the endwall surfaces or the blade surfaces, or both. 

*************************************************************************** 

## **Return to card BLD2  for the next bleed patch on the current blade row.** 

*************************************************************************** 

*************************************************************************** 

## **Return to cards  BLD1 to input  bleed data on the next blade row.** 

*************************************************************************** 

## **End of all bleed flow data return to the main data input.** 

*************************************************************************** 

## **SHROUD LEAKAGE DATA** 

*************************************************************************** *************************************************************************** 

## **Insert here the cards which define the shroud leakage for each blade row for which KTIPS   is less than zero.** 

*************************************************************************** *************************************************************************** 

## **FOR N = 1 to NROWS insert cards  SHRD1 to SHRD3 .** 

**Cards SHRD1  to SHRD3 are only needed if KTIPS is less than zero for this row.** 

## **CARD SHRD1 .** 

KSHROUD, JLEAKS, JLEAKE, JLKINS, JLKINE 

KSHROUD The K value where leakage takes place, set = 1 for hub leakage, = KM for tip leakage. JLEAKS The J value where the leakage starts, this is relative to the J value at the start of the current blade row. JLEAKE The J value where the leakage ends, this is relative to the J value at the start of the current blade row. JLKINS The J value where the leakage flow starts to re-enter the main flow. this is relative to the J value at the start of the current blade row. JLKINE The J value where the leakage flow finishes re-entering the main flow. this is relative to the J value at the start of the current blade row. 

Note the leakage is extracted uniformly over the area of extraction between JLEAKS and JLEAKE  and re-injected uniformly over the area of injection between JLKINS  and JLKINE. 

Note that shroud leakage flow from downstream of the blade to upstream, as in compressors, can be handled. In this case JLEAKS and JLEAKE should be greater than JTE, and JLEAKINS and JLEAKINE should be less than JLE. 

*************************************************************************** 

## **CARD SHRD2 .** 

SEALGAP, NSEAL, CFSHROUD, CFCASING 

SEALGAP The seal clearance in metres. NSEAL The number of shroud seals (fins). CFSHROUD The skin friction coefficient on the shroud outer surface, this is rotating at the same speed as the blade row. Typical value = 0.005. 

CFCASING The skin friction coefficient on the endwall surface adjacent to the shroud. This could be the hub or casing, typical value = 0.005. 

*************************************************************************** 

## **CARD SHRD3 .** 

WCASE, PITCHIN 

WCASE The rotational speed of the hub or casing adjacent to the shroud in RPM. This will always be zero for the casing but could be the machine rotational speed for the hub. 

PITCHIN The angle in the meridional plane at which the leakage flow re-enters the mainstream. The  angle is measured from a tangent to the hub or casing and is always treated as positive. In degrees. Guess it = 45deg if the angle is not known. 

*************************************************************************** 

## **Return to Card  SHRD1  for shroud leakage on the next blade row for which KTIPS is negative.** 

*************************************************************************** 

*************************************************************************** *************************************************************************** 

## **End of shroud leakage data. Return to the main data input.** 

*************************************************************************** *************************************************************************** 

## **NOTES ON THE INPUT DATA** 

## **Note 1 INLET BOUNDARY CONDITIONS** 

**IN_PRESS** is used to specify the boundary condition on the static pressure at inlet. 

If  IN_PRESS = 0 , the inlet pressure is calculated from the inlet density, which is calculated directly by the solver, and an assumption of locally isentropic flow from the inlet stagnation conditions. In this case higher values of RFIN, typically = 0.5, can usually be used. 

If  IN_PRESS  =  1,  the inlet pressure is linearly extrapolated along the grid lines from the interior flow field assuming   d[2] P/dm[2  ] = 0. 

If  IN_PRESS  =  3 the upstream boundary condition is as with IN_PRESS  = 1 but the pressures are circumferentially averaged before extrapolation. This may be used to cure an instability which sometimes occurs at the inlet boundary.  This instability takes the form of a saw tooth wave along the inlet boundary and usually seems to occur when the grid is highly distorted (i.e.  skewed) at inlet. 

If  IN_PRESS = 4  then the boundary condition is as with IN_PRESS =  1 but  the inlet static pressure is taken to be uniform over the whole inlet boundary and is taken from the pressure extrapolated at the mid-span and mid-pitch  point. This option may be useful for calculating flows with a strong velocity gradient in the inlet as it prevents failure if the inlet velocity reverses locally. 

Boundary conditions which use d[2] P/dm[2] =0, i.e.  IN_PRESS = 1 , 3 or 4  require a lower value of the inlet pressure relaxation factor, RFIN. Typically RFIN = 0.1 in such cases. 

IN_PRESS = 0 is generally preferred for axial flow machines. 

The inlet pressure and the specified inlet stagnation pressure and temperature are used, together with the assumption of isentropic flow, to compute the absolute velocity at inlet. This is then resolved into the velocity components according to IN_VTAN  and IN_VR. 

**IN_VTAN** is used to specify the type of boundary condition on the inlet flow direction on the blade-blade stream surface  (i.e. on tan[-1] (Vθ/Vm)). 

If  IN_VTAN  =  0,  the absolute flow angle is held fixed at the value  given by BS(K) . In degrees,  card 77. 

If  IN_VTAN  =  2,  then the relative flow angle is held fixed and  =  BS(K). In degrees, card 77 . 

If  IN_VTAN  =  1, then the absolute swirl velocity is held fixed and equal to VTIN(K)  , card 75, in m/sec.  and the value of BS(K) is ignored. 

IN_VTAN = 0 is usually the best condition for both fixed and rotating blade rows. 

IN_VTAN = 1 should be used if the relative inlet flow is supersonic since the unique incidence condition then applies and a fixed flow direction may then be unstable. 

**IN_VR** is used to specify the inlet boundary condition on the radial velocity at inlet. 

If INVR  = 0 then the radial velocity at inlet will be obtained by extrapolation from the interior flow field  Vr(1) = Vr(2) ,  and the value of BR(K) will be ignored although it must still be input. 

If  IN_VR = 1 then the radial velocity at inlet is obtained from the meridional velocity and the input value of meridional pitch angle, BR(K), card 78. 

If the radial velocity is expected to change with meridional distance, as in radial flow machines. Then IN_VR = 1  must be used as  Vr(1) = Vr(2)  is not physically realistic and so is likely to be unstable. 

It is important that the specified pitch angle on the endwalls is compatible with the endwall slope, as determined by the annulus geometry. If this is not the case local instability may occur. 

## **NOTE 2 EXIT BOUNDARY CONDITIONS** 

The usual exit boundary condition is a specified static pressure. This spanwise variation in static pressure is determined by IPOUT. 

If IPOUT = 1  then the exit pressure is input a both hub and tip and a linear variation with span is assumed. 

If IPOUT = 0  then the pressure is fixed at the hub and the spanwise variation is obtained from radial equilibrium, assuming no streamline curvature. 

If IPOUT = -1 the pressure is fixed on the casing and the spanwise variation is obtained from radial equilibrium assuming no streamline curvature. 

If IPOUT = 3 the spanwise variation of exit pressure is input as data in card 73. 

These options fix the spanwise variation in pitchwise area averaged pressure at exit. The pitchwise variation in the exit pressure is obtained by extrapolating from the next upstream grid point. The proportion of the upstream pressure variation that is imposed on the exit boundary is FEXTRAP which is input in card 19. This extrapolation allows pressure waves to interact with the exit boundary with little reflection. A typical value of FEXTRAP is 0.8 or 0.9 . 

In some cases the flow tries to reverse at the exit boundary, i.e. to try to enter through it. This is always unstable as there are no boundary conditions to give the properties of the entering fluid. There are several possible ways of overcoming this. The simplest method is to apply high smoothing near the boundary so as to make the flow more uniform. This is done by SFEXIT and NSFEXIT in card 23. Typical values are SFEXIT = 0.1, NSFEXIT = 5 but either may be increased to give a more powerful smoothing. 

An alternative method is to model a perforated plate or wire mesh at exit. The resistance of the mesh will cause the flow through it to be more uniform and should remove any tendency to reverse flow. This option is chosen by setting PLATE_LOSS in card 24 as the pressure loss coefficient of the plate, which the pressure drop through it divided by the upstream dynamic head. A value 0f 2,0 should make a non-uniform flow closely uniform. 

A further option is to model a throttle at exit. This is mainly used to obtain solutions for compressors near their stall point. At the stall point the mass flow varies very rapidly with exit pressure, inevitably leading to instability at conditions very close to the stall point. To overcome this the exit pressure may be made to vary with the exit mass flow along a parabolic curve passing through a prescribed point with mass flow = THROTTLE_MAS  and static pressure = THROTTLE_PRES. This simulates the presence of a throttle downstream of the calculation domain. A simple choked throttle would have a mass flow directly proportional to the exit stagnation pressure but it was found that a steeper curve gave better results and so the parabolic variation of pressure with mass flow was chosen. The final solution should lie at the intersection of the machine characteristic and the throttle line so the steeper the line the closer should be the mass flow to the required mass flow. If this option is chosen then THROTTLE_EXIT must be set = 1 in card 24 and then THROTTLE_PRESS, THROTTLE_MAS and RF_THROTL  must be input in card 25 . 

A new exit boundary condition is included in Version 19.2. The changes in pitchwise average static pressure at the downstream boundary are brought about by a series of one-dimensinal pressure waves. These are based on the method of characteristics so they change the density, velocity and energy as well as the pressure. The pitchwise variation in exit static pressure is extrapolated from upstream by fraction FP_XTRAP, typical value = 0.9.  The fraction of the required change in pitchwise average pressure that is added on each time step = FRACWAVE whose typical value = 0.25 .  FP_XTRAP  and FRACWAVE are input as extra data in CARD 23. 

The new exit boundary condition is only available if using “NEW_READIN” data input format. 

The new boundary condition is used if FRACWAVE is greater than zero. If FRACWAVE = zero or its value is not included in CARD 23 then the original boundary condition is used. Old data sets which do not include FP_XTRAP  and FRACWAVE  will still run and will use the old boundary condition. The options IPOUT = -1, 0, +1  or +3  can still be used to fix the pitchwise average exit pressure with the new condition. 

It is thought that the new boundary condition is better than the original one in that it causes less interference between the pitchwise variation in exit pressure and the upstream flow, this is particularly desirable when pressure waves are intersecting the downstream boundary. It should therefore be regarded as the preferred exit boundary condition. Three new test cases which include this effect are added to the selection of test cases. These are all named  ***-19.2.dat 

## **NOTE 3 TIME STEP OPTIONS** 

CFL  is the timestep multiplying factor and is the main parameter controlling stability of the program.  The length of timestep taken is given by  Δt  =  CFL.Δs/a0  where  Δs  is the minimum length scale of a cell  and  a0  is the local speed of sound at inlet. 

Local time stepping is always used based on the length scale of each cell and the local average relative Mach number in the cell. The time steps are updated every 5 steps using the current Mach number. 

For the “scree” scheme values of  CFL =  0.4 -> 0.5  are typical.  To give a margin of safety it is usual to start with CFL = 0.4 and only to increase it if this is stable. 

For the SSS scheme values of CFL = 0.7 are typical. Larger values are often stable but may give oscillatory residuals without causing failure. In such cases the solution is usually perfectly acceptable. 

## **Values of CFL less than  0.2  should never be needed.** 

## **If problems with stability occur then the first remedy tried should be a reduction in CFL.** 

ITIMST determines the type of time step to be used.  The standard option is ITIMST = 3 which means that the timestep is evaluated for each individual cell, using the cell dimensions and Mach number, and the standard “scree” scheme is used. 

If ITIMST = -3  then the time step is evaluated as above but the SSS scheme is used. 

If ITIMST = 4 or  -4  then SSS scheme is used and the coefficients are read in as data. 

If ITIMST = 5 then the low Mach number option is used with the standard “scree” scheme. This uses artificial compressibility to calculate the pressure from an artificially low speed of sound, which is input as data. This speed of sound should be about twice the maximum relative velocity expected in the flow. 

If ITIMST = -5  then the low Mach number option is used with the SSS scheme. 

If ITIMST = 6 then artificial compressibility is used with fully incompressible flow. The required density is read in as data. 

If ITIMST = -6  then the incompressible option is used with the SSS scheme. 

## **NOTE 4    ARTIFICIAL VISCOSITY OR SMOOTHING FACTORS** 

The smoothing factor **SFT** controls the smoothing in the pitchwise and spanwise directions and **SFX** controls that in the streamwise (meridional) direction. The smoothing applied is always combined second and fourth order smoothing with the proportion of 4[th] order being input as FAC_4TH .  Hence the smoothing applied to the primary variables is 

SFX*(1- FAC_4TH) *(second order value)  + SFX*FAC_4TH * (fourth order value) 

Typical values of  FAC_4[TH] are  0.8  with higher values giving less artificial viscosity. 

Low values of  SFT  and SFX which are approximately equal to  0.01 x CFL  will usually provide stability with negligible 'viscous' effect from the smoothing. Hence with CFL = 0.4 the smoothing factors would typically be 0.004  . Lower values are usually stable and give even less influence of the artificial viscosity. 

The input values of SFT and SFX  are  scaled by CFL/0.5  before they are used. 

An increase of smoothing should be the second resort  (after reducing  CFL)  if signs of instability occur. 

The values of  SFT  and  SFX  may be  automatically increased during the first NCHANGE steps to help overcome initial transients. The increase is  0.02  on starting and decreases to zero after NCHANGE steps. Typically NCHANGE = NMAX/4 . 

## **NOTE 5   NEGATIVE FEEDBACK TO LOCALISE ANY INSTABILITY** 

**DAMP** controls the amount of negative feedback. 

The maximum change of the variables in any cell on every iteration is limited if its magnitude is  comparable to or greater than  [ DAMP  x  (the average change of the variable concerned)]. This prevents local instabilities, such as might occur during the initial transient, growing and causing failure of the whole calculation. It should have no effect at all on the steady solution. 

A value of  DAMP  =  10  is usually acceptable and should be regarded as standard.  Low values (= 5 ) give greater stability but sometimes produce incorrect results, e.g. premature convergence,  and so should be used with caution. Higher values of  DAMP  will produce faster convergence and  DAMP  > 25  means that damping has very little effect and may be used with caution if the initial transients are weak. 

If the value of DAMP is set to be greater than 100 then the damping is not used. This is usually possible with the “scree” scheme. However, use of DAMP will give usually faster convergence with no loss of accuracy. 

The value of DAMP is be automatically increased during the first NCHANGE steps in the same way as SFT  and SFX. 

## **NOTE 6 PITCHWISE AND SPANWISE GRID SPACING** 

**FR(K)  and  FP(I)** control the **relative** spacing of the grid lines in the spanwise and pitchwise directions respectively.  Only the **relative** spacings are needed and the values input are then divided by their sum to give the fraction of the height and gap occupied by each element. 

The change in relative spacing between adjacent grid points should not be greater than about 30% ,  i.e.   F(I+1)/F(I)  < 1.3 ,  because the  smoothing routines assume uniform spacing and will produce numerical errors for highly non-uniform spacing. Lower values than this, say 1.20,  are really preferable, especially when fine grids, i.e. a large number of pitchwise or spanwise grid points, are used. 

The streamwise grid spacing (J direction) should also not vary by a factor of more than about 1.3 between adjacent points. Again an expansion ratio of about 1.20 is preferred. 

Overall very large variations  (~ 50:1) in grid spacing may be used as long as the spacing is changed gradually as described above. 

Highly non-uniform grid spacing with the ratio of maximum to minimum spacing = about 20 are usual for viscous calculations. The larger this ratio and the larger the expansion ratio the more closely the grid points will be clustered in the boundary layers. 

The grid spacing is generated automatically within the program if FP(3) or FR(3) is set equal to zero. In this case the spacing is varied as a geometrical progression away from both walls with a ratio FR(1) or FP(1) between adjacent points up to a maximum spacing  = FR(2) or FP(2) times the spacing at the wall. The same expansion ratio and same maximum are used away from the other wall. The other values of FP and FR must still be input but are not used and so can be set equal to zero. For example when using this option the values of FR(K) might be: 

FR(1)  =  1.2 FR(2)  = 25.0 FR(3)  = 0.0 All other values of FR(K) = 0.0 

This will give a grid expansion ratio of 1.2  up to a maximum value of 25. All other values of FR(K)  from K = 4  to  K = KM-1 (or FP(I) from I = 4 to IM-1) must be input but are not used and so can be set equal to zero. 

Use of too high a grid expansion ratio is one of the most frequent mistakes made by users of the program. 

## **NOTE  7 OUTPUT FILES** 

IOUT(I)  where  I = 1 to 13,  determines which flow variables are to be sent to the file “results.out”  on convergence or when output is requested via  NOUT. This is a formatted file and so may be inspected on the screen or printed out . 

IOUT(I)  =  1 or 3  gives a full printout of the I'th  variable, 

IOUT(I) =  0  gives no printout. 

OUT(I)  =  2 gives a printout of the circumferentially mass averaged value of the variable. 

The variables are only written to the file at spanwise grid point (K)  where  KOUT(K) = 1. If KOUT(K) = 0 they are not output. 

The variables are numbered as follows : 

|1|=|Percentage change in Vm|
|---|---|---|
|2|=|Axial velocity|
|3|=|Absolute swirl velocity|
|4|=|Radial velocity|
|5|=|Static pressure|
|6|=|Relative Mach number|
|7|=|Absolute stagnation temperature|
|8|=|Meridional velocity|
|9|=|Swirl angle tan-1(Wq/Vm).|
|10|=|Meridional pitch angle tan-1(Vr/Vm)|
|11|=|Density|
|12|=|Ratio of P/ T**(γ/(γ-1)) to the inlet value at mid-span|
|||and mid-pitch. This should =1.0 for isentropic flow and|
|||can be thought of as the ratio of the local stagnation|
|||pressure to that that would be obtained in an insentropic|
|||process to the same temperature.|
|13|=|Pressure coefficient (P-PIN)/(P01-PIN)|



The above output is sent to the file  “results.out”  on fortran unit 3 but **a printed output file is very long** and is not usually very useful. Graphical inspection of the output is much more efficient. The program can easily be edited to write out other properties if required. 

A separate output file called “flow.out” is automatically sent to Fortran unit 7 on completion of a run. This file contains the primary flow quantities, which can be used to compute any other flow quantity. The file is unformatted and may be read and plotted by a plotting program, it should be straightforward to interface it to different plotting routines, it is also used as a restart file. An unformatted  file called “grid.out”  is automatically written to Fortran unit 21  and is also used for plotting but not for the restart. 

A formatted file called "global.plt"  used for plotting some one-dimensional mass averaged flow quantities against meridional distance is sent to Fortran unit 11. 

A formatted file named “stage.log” is sent to Fortran unit 4  and may be used for plotting the convergence of the calculation against time step number. 

A formatted file called “loss-co.plt” contains the loss of isentropic efficiency at every “J’ station, based on the local mass averaged flow, is written to Fortran unit 23 at the end of any run and is used to plot lost efficiency against meridional distance. 

A formatted file called “mixbconds”  is written to Fortran unit 12.  This contains the mixed out values of the flow properties at each mixing plane at every spanwise (K)  grid point. It may be used to provide the inlet boundary conditions to a subsequent calculation on an individual blade row or smaller group of blade rows. 

The plotting programs that use some of these files are based on the Hgraph plotting package and so are not publicly available. 

## **NOTE 8 MULTIGRID  LEVELS** 

Three levels of multigrid are available in the standard program.  Unlike most multigrid methods the block sizes used do not need to be increased in multiples of 2, in fact any block sizes can be used but multiples of 3 seem to be about optimum. 

IR, JR, KR  are the number of individual elements along the  I,J,K  sides of the smaller multigrid blocks. 

IRBB, JRBB, KRBB are the numbers of individual elements along the  I,J,K  sides of the larger blocks. 

If  IR, JR, KR  are  all  = 1,  then the multigrid  is not used . 

It is preferable but by no means essential to use an integral number of blocks in each coordinate direction i.e. (IM-1)/IR, (IM-1)/(IRBB),   (JM-1)/JR,  (JM-1) /(JRBB),  (KM1)/KR, and  (KM-1) /(KRBB) should all be integers. 

The optimum block size depends on the problem, but  IR, JR, KR, all = 3 seems good,  as does IRBB, JRBB, KRBB  all  = 9 . With these values suitable values of IM  and KM would be 19, 28, 37, 46, 55, 64, 73 or 82 . The value of JM is not so critical. 

A third level of multigrid is formed from one-dimensional blocks which fill the whole pitch and whole span. This is highly beneficial in speeding up convergence as it allows information to be transmitted from outlet to inlet (and vice-versa) in a few time steps.  The block sizes for this are generated automatically without any user input. Four of these “superblocks” are generated, one upstream of the leading edge, two within the blade row and one downstream of the trailing edge.  If this third level of multigrid is used then the second level blocks should not also fill the whole pitch and span and so it may be desirable to use rather smaller blocks for the first two levels of multigrid. 

The time steps used for the multigrid blocks are estimated within the program but the theoretical values need to be reduced to ensure stability. The scaling factors on the changes produced by the multigrid are input as data in card 17. The greater these are the faster will be convergence but the greater the tendency to instability. Hence the values should be significantly less than unity. Typical safe values are FBLK1=0.4, FBLK2=0.2 and FBLK3=0.10 , although larger values can often be used and if a calculation is going to be repeated many times it might be worth experimenting with higher values.  The third level of multigrid is sometimes prone to instability and should not be used with too high a scaling factor. A factor 0f 0.1 is usual. 

## **NOTE  9 STREAMWISE SURFACES FOR BLADE GEOMETRY INPUT.** 

The streamwise or cylindrical surfaces on which blade section data is input are not necessarily true stream surface and are usually not the same as the surfaces which are used for the computational mesh.  The blade geometry is input on NSECS_ROW surfaces and is then interpolated onto NSECS_IN evenly spaced stream surfaces. In most cases NSECS_ROW and NSECS_IN will be the same. The program will then interpolate in the NSECS_IN surfaces to set up the calculation mesh with KM streamwise grid lines spaced as determined by FR(K). The interpolation will be less accurate if the spacing of the input stream surfaces does not vary smoothly and so the spacing between input stream surfaces should change monotonically so that a graph of spanwise distance against input surface number is a smooth curve. 

IF INSURF = 0 then the first and last of the input surface will be the hub and casing respectively. **This is strongly preferred.** If INSURF = 1 then the hub stream surface may be input as a separate table of coordinates and the intersection of this with the quasi-orthogonal lines of the other stream surfaces is found. If INSURF = 2 then the casing stream surface is input as a separate table. If INSURF = 3 then both hub and casing stream surfaces are input in this way. 

It is strongly preferred that the first input section should be on the hub and the last section on the casing of the machine. However, the hub and casing shapes can be input separately using INSURF = 1, 2 or 3. In which case the program will find the intersection of the quasiorthogonal lines with the hub and casing but this procedure is of limited accuracy and should be avoided if possible. 

The number of sections required depends on how much the blade geometry changes along the span. At least two sections are needed and that is sufficient for a blade with linear variations in section. More than 5 sections are seldom required even for highly twisted blades. 

For a quasi-3D calculation, with KM = 2, then only one stream surface is input and the other surface is generated from a table of stream surface thickness against fraction of meridional distance. 

The points at which the blade coordinates are input on each streamwise surface determine the intersection of the quasi-orthogonal surfaces (J = constant) with that section, and so the number of input points (JM) must always equal the number of quasi-orthogonal surfaces (JM).  Similarly, the leading edge point (JLE)  and trailing edge point  (JTE)  must be the same on all surfaces. The relative spacing of the  J  points along each surface should also be similar on all surfaces since the quasi-orthogonal surfaces need to intersect the meridional plane in a smooth curve to allow good interpolation. 

## **NOTE 10 DIMENSIONS OF DATA AND VARIABLES** 

The program works with dimensional quantities. Physical dimensions of input coordinates and fluid properties should always be consistent **.** If the dimensions are in metres then all fluid properties must be in SI units. However, for a single stationary blade row the dimensions of the blade do not affect the magnitude of the velocities and so any convenient units may be used for the blade coordinates. The input geometrical data can be scaled by FAC1, FAC2  and FAC3 and this allows the data to be converted from any other units to metres if necessary. 

If it is desired to use British units then **they must be consistent,** if lengths are in  ft  then pressures must be in poundals/sq ft and temperatures in degrees R and the gas specific heat in ft poundals/ deg R. 

## **NOTE  11 SPECIFICATION OF THE MASS FLOW RATE** 

**IN_FLOW** in  Card 22 may be used  to obtain a specified mass flow as input in card 26. This option is not generally used as the mass flow forcing introduces artificial changes of stagnation pressure. 

If IN_FLOW  =  3, Then the required mass flow rate for the whole annulus or machine, in kg/sec, is read in Card 26. 

If IN_FLOW  =  2, Then the local mass flow is forced towards the current average mass flow .  This may give faster convergence whilst the final mass flow should still be fixed by the pressure ratio. 

If IN_FLOW  =  0 Then the mass flow is determined by the input pressure ratio as is usual for Euler and Navier-Stokes solvers and is not forced in any way. 

The mass forcing function is damped by a factor  RFLOW, input in Card 26,  for which a typical value is  0.1  . However, when using IN_FLOW = 2, lower values of RFLOW, say = 0.01, should be used as high values can cause spurious entropy changes even when the mass flow is only forced towards the average value.. 

When this option is used then the stagnation pressure change will be adjusted to make the mass flow and specified pressure ratio compatible and conservation of stagnation pressure (or entropy) cannot be expected.  Hence the calculated efficiency will not be correct when IN_FLOW = 3 is used. 

IN_FLOW =0 should be regarded as standard. However, IN_FLOW =2 may give faster convergence, especially for centrifugal compressors. IN_FLOW=3 should not be used unless the mass flow expected is known reasonably accurately, however, in difficult cases it may be used to provide a good initial guess as a restart file. 

## **NOTE 12 USE OF ISHIFT TO MATCH THE GRIDS AT MIXING PLANES** 

This is a special option for shifting the coordinates of the input data for multi-blade row calculations so that the grids become contiguous at the mixing planes. 

IF ISHIFT = 0  then the grid coordinates are used as read in with no changes. **Note this option must be not be used unless the mixing plane and next downstream plane were made coincident in the raw data.** 

If ISHIFT =1 then the axial coordinates of all but the first blade row are automatically shifted from their input values to make the blade rows line up on the hub stream surface so that the first grid point on one row is coincident with the last grid point on the upstream row. Note that only the axial coordinates on the hub are shifted so that the radial coordinates must already be compatible, hence the option must be used with great care especially on radial flow machines. 

If ISHIFT = 2 then the blades not shifted but the grid spacing is made to vary geometrically between the trailing edge of one blade row and the downstream mixing plane and between the leading edge of the next row and the upstream mixing plane. The mixing plane and the next downstream plane are automatically made to be coincident as is necessary. This option gives a good grid between the blade rows. If it is required to shift the blades before forming the grid this can be done using XSHIFT and RSHIFT in Cards 58  and 64. 

If ISHIFT = 3 the grid spacing is again made to vary geometrically between the trailing edge of one blade row and the downstream mixing plane and between the leading edge of the next row and the upstream mixing plane, exactly as with ISHIFT = 2.  However, in the meridional view, the grid will be formed by straight lines (conical stream surfaces) joining the trailing edge of one blade row and the leading edge of the next row. This is also applied to the hub and casing and so can cause small changes of annulus geometry. This option is necessary when the surfaces on which the blade geometry is input are not continuous at the interface plane. i.e. different surfaces are used in different blade rows. This is often the case if the data input is on cylindrical surfaces. 

If ISHIFT = 4 is the same as ISHIFT = 3  but the hub and casing shapes are not changed, i.e. they are not made conical surfaces. This is better than ISHIFT = 3 unless the hub or casing shapes are discontinuous. 

## **The use of ISHIFT = 2 or = 4 is strongly recommended.** 

## **NOTE 13 GRID EXTRAPOLATION UPSTREAM AND DOWNSTREAM OF A BLADE ROW WHEN ISHIFT IS  NOT = 0 .** 

When a new grid is generated between blade rows by using ISHIFT = 2, 3 or 4 then the slope of the periodic boundary (I=1 and I=IM) upstream and downstream of the blade can be obtained either by extrapolating the blade centre line or by inputting the grid angles as data. The choice between the two methods is determined by IF_ANGLES in CARD 52. 

If the option to extrapolate the blade centerline is chosen, i.e.  IF_ANGLES = 0,  then the extrapolation is from a point  NEXTRAP_LE  grid points downstream from the leading edge to the leading edge and from a point  NEXTRAP_TE  points upstream of the trailing edge to the trailing edge.  NEXTRAP_LE   and NEXTRAP_TE  are input in CARD 34 and are usually taken to be 10 , but this may need to be increased for a highly cambered leading or trailing edge. This is the usual option. 

In some cases the blade centre line is highly curved at the leading or trailing edges and the above extrapolation may give an incorrectly aligned grid.  In such cases the angle of the grid to the meridional direction (i.e. to a line of constant theta coordinate) can be read in as data in CARD 66.  BETAUP is the grid angle upstream of the leading edge. Downstream of the trailing edge the grid angle varies from BETADWN1 at the trailing edge to BETADWN2 at the downstream mixing plane or downstream boundary.  In most cases BETADWN2  and BETDWN1  will be closely equal. This option is chosen if  IF_ANGLES in Card 52 was greater than zero. 

The grid angles are positive if a vector in the direction of the angle has a positive component in the circumferential (theta) direction. 

## **NOTE 14 DEFINITION OF COOLING FLOWS AND OF DIRECTION OF EJECTION** 

The cooling flows may be ejected through "patches" on the blade and endwall surfaces.  The I, J and K grid points covered by the patch are input as data. The coolant stagnation temperature, stagnation pressure and direction of ejection are taken to be constant over each patch. The stagnation temperature and pressure that are input are those at which the coolant is supplied to the blade, which will usually be at a lower radius than its point of ejection. The increase of stagnation temperature and pressure due to work done on the coolant by a rotating blade is calculated within the program using the input values of the coolant supply angular momentum (RVT_IN)  and disc rotational speed (RPM_COOL). 

In versions earlier than 18.3  only the option IFCOOL = 1 is available. 

IF IFCOOL = 1 then the coolant velocities are determined by the input stagnation temperature and Mach number and do not change through the calculation. The velocity of ejection **relative** to the blade is then calculated from the specified **relative** Mach number of the flow leaving the cooling holes. The coolant velocity is uniform over the patch and the stagnation pressure, which is input, is not used except to calculate the efficiency. The subroutine COOLIN_1 is only called once in this case and so uses negligible CPU time. 

In version 18.3  and above  the option IFCOOL =2 is available. 

IF IFCOOL = 2 then the coolant velocity is determined by the input stagnation pressure and temperature and the local static pressure on the coolant patch. It therefore varies over the patch and through the calculation. The change in stagnation pressure due to pumping work on the coolant as it flows through a rotating blade is estimated and used in the calculation of the ejection velocity and overall efficiency. The coolant ejection Mach number, which must still be input, is not used in this case. The subroutine COOLIN_2 is called every 5 time steps and so uses slightly more CPU time in this case. 

The direction of the cooling jet leaving the blades and endwalls is specified by two angles. The first angle is that between the coolant jet and a plane tangent to the surface through which it is being ejected.  This is more easily visualised as (90°  - the angle between the coolant jet and the local normal to the surface). See Fig 20a. The second angle is that between the projection of the coolant jet onto the surface and a line in the surface. The definition of this line differs for blade surface or endwall ejection as described below. 

For ejection through the blade suction or pressure surfaces the line is a line of constant radius in the surface, i.e. the intersection of the blade surface with a cylindrical surface. See Fig 20b. The angle is positive if the radial component of the jet velocity is positive. 

For ejection through the hub or casing the line is a line of constant circumferential angle, θ, drawn on the hub or casing, i.e. the intersection of the hub or casing with a plane of constant circumferential angle  θ passing through the machine axis. This angle is positive if the circumferential (theta) component of the jet velocity is positive. 

**==> picture [298 x 77] intentionally omitted <==**

**----- Start of picture text -----**<br>
Jet<br>Cooling jet<br>Normal to surface<br>Angle of jet<br>to surface<br>Tangent to surface<br>**----- End of picture text -----**<br>


Fig 2oa . Definition of the angle of the coolant jet to the blade  or endwall surface. 

**==> picture [272 x 257] intentionally omitted <==**

**==> picture [210 x 207] intentionally omitted <==**

Fig 20c. Endwall Coolant ejection angle. 

These definitions of cooling flow direction have been chosen because they can be easily applied to both axial and radial flow machines. 

## **NOTE 15     USE OF A TRAILING EDGE CUSP** . 

If a fine grid is used around a blunt trailing edge (TE) it is usually found that the flow does not separate soon enough at the start of the trailing edge circle. This leads to a locally low pressure as the flow follows the highly curved surface and gives an unrealistic loading of the TE. Usually this produces a negative load at the TE due to too low a pressure on the pressure surface. In practice it is always found that, in subsonic flow, the loading falls to zero at the TE. 

To overcome this problem it is recommended that a cusp is fitted to the TE.  The cusp is a triangular region behind the TE , as shown in the figure below, which may be regarded as an extension of the blade surface, except that flow can pass through it. The cusp is made to carry no tangential force and so does not contribute to the lift on the blade or the work done by it. However, it does exert a meridional force on the blade, which is exactly balanced by the force it exerts on the flow. This force can be thought of as a base pressure x the tangential thickness of the TE. 

The portion of the blade upstream of the trailing edge is modified so that any high curvature due to the trailing edge circle is removed and the smooth surfaces before the start of the curvature are extrapolated to the trailing edge point. The trailing edge point will then have a finite thickness and this forms the base of the cusp. The cusp can then be aligned with either the blade centre line (most usual) or with either blade surface and its length can be input in terms of the number of grid points on it. A cusp is chosen by setting IFCUSP = 1 in Card 52. 

If  IFCUSP = 1 then ICUSP, LCUSP  and LCUSPUP  are input in the next card, Card 53. ICUSP = 1 The cusp is aligned with the I=1 blade surface ICUSP = -1 The cusp is aligned with the I = IM blade surface ICUSP = 0 The cusp is aligned with the blade centre line. This is the usual choice. LCUSP  Is the number of cells on the cusp. LCUSPUP The cusp starts this number of grid points upstream of the trailing edge. 

**==> picture [147 x 221] intentionally omitted <==**

## **NOTE 16 USE OF A BODY FORCE TO MAKE THE FLOW SEPARATE AT A THICK TRAILING EDGE** 

It is difficult to use a cusp on a blade row with a very thick trailing edge but if the grid is refined around the trailing edge (TE)  the flow will usually not separate soon enough, leading to a locally low pressure on the pressure surface and negative blade loading at the TE. This is not physically realistic and in practice the flow usually separates at the start of the trailing edge circle (blend point). To try to overcome this a TE separation can be forced by a body force field allowing a fine mesh to be used around the TE. This is invoked by setting IFCUSP = 2. 

The body force is applied over a region defined by NSEP_I1, NSEP_IM, N_WAKE  and SEP_THICK all of which are input in Card 54. 

NSEP_I1 is the number of grid points upstream of the TE from which the blade I = 1 surface is extrapolated. NSEP_IM is the same for the I = IM  surface .  The force field extends N_WAKE grid points downstream of the trailing edge point , JTE , this value may be negative to stop the force field before the TE.  The body force is applied over a region which is more than (SEP_THIK x local blade thickness) **inside** the extrapolated region.  The magnitude of the body force is proportional to 

(1 – SEP_DRAG) and it acts in the direction of the local velocity.  Typically SEP_THIK = +0.01 (it may be positive or negative) and SEP_DRAG = 0.99 . Lower values of SEP_DRAG lead to virtually stagnant flow in the affected region. 

**==> picture [361 x 287] intentionally omitted <==**

**----- Start of picture text -----**<br>
Fig 15a. A fine grid around a thick trailing edge.<br>**----- End of picture text -----**<br>


The body force is applied over the shaded region as illustrated below. The region may be made wider in the pitchwise direction by making SEP_THIK  negative. 

**==> picture [383 x 261] intentionally omitted <==**

**----- Start of picture text -----**<br>
Body force is<br>applied over<br>the shaded<br>region<br>Fig 15b. Extent of the body force<br>field.<br>**----- End of picture text -----**<br>


In practice this option is seldom used. It is easier to use a cusp with the option to extrapolate the blade surface from upstream of the TE, so that there is no large change of curvature of the blade surface and the TE itself has a finite thickness, then to form a cusp over several grid points downstream of the TE. 

## **NOTE 17** THE MIXING PLANE MODEL 

Development of a good mixing plane model is one of the most difficult problems in CFD. The mixing plane is an artificial concept designed to permit steady calculations of blade rows which are in relative motion due their rotation. It is generally assumed that the mixing plane should allow the flow from an upstream blade row to mix out as if it were doing so in a long duct with constant area and it should allow the flow to enter the downstream row as if it had originated from a pitchwise uniform flow far upstream. Hence the mixing plane must transmit the mixed out fluxes of mass momentum and energy from one blade row to the next whilst causing the minimum distortion to the pitchwise non-uniform flows leaving the upstream row and entering the downstream row. The mixing out of a non-uniform flow to a pitchwise uniform flow is generally an irreversible process and although the fluxes of mass, momentum and energy must be conserved in the mixing process the entropy will usually increase. This increase in entropy represents the mixing loss which occurs in the real flow. However, It should be emphasised that this is only a model of reality and it is not obvious that the mixing loss, which occurs in the unsteady flow in a real machine, is the same as that at the mixing plane. 

Several different mixing plane model have been used during the development of MULTALL. The latest one in MULTALL-14.6, MULTALL-15.2 and MULTALL_OPEN  is thought to be the best yet. It is a combination of the latest one used in TBLOCK, which is robust and permits reversed flows across the mixing plane, with the flux extrapolation method used in earlier versions of MULTALL. The same model is now used in both MULTALL and TBLOCK. 

As in all previous versions there are two coincident “J’ grid surfaces at the mixing plane. These are numbered  JMIX  and  JMIX+1. All flow properties are pitchwise uniform and equal on both of these faces, although they will vary in the spanwise (K) direction. The pitchwise uniform value is the mixed out value. The values are made equal on both surfaces by treating the flow from JMIX to JMIX+1 as if it were between two faces of a onedimensional finite volume cell, which extends over the whole pitch, and time stepping the flow between them, exactly as for the cells in the rest of the grid. This ensures that when the solution is converged the fluxes on the two coincident surfaces become equal. Since the flows are pitchwise uniform this makes all the flow properties equal on the two faces. 

The upstream and downstream faces of the mixing plane are decided by checking the flow direction on each spanwise (K) grid surface and the direction can change from one surface to the next. There is no presumption that the flow is in the positive J direction. Hence the model can allow any amount of reverse flow. 

For the cells upstream of the mixing plane, i.e. , assuming that the flow is in the positive J direction, those between JMIX-1  and JMIX, the fluxes on their upstream face are calculated as usual but the fluxes on their downstream face, i.e. on the mixing plane, JMIX, are obtained by flux extrapolation. If the upstream face is  JMIX-1, this involves adding a fraction of the difference between the local flux and the pitchwise averaged flux at JMIX -1  to the flux calculated from the uniform flow at JMIX.  i.e. 

FLUXjmix = FLUXavg,jmix  + FEXTRAP x (FLUXjmix-1 – FLUXavg,jmix-1) 

Hence the cells between JMIX-1  and JMIX  “see” only a fraction  (1-FEXTRAP) of the uniform flux at the mixing plane.  FEXTRAP is input as data and a typical value is 0.8 - 0.9. The more closely the grid lines JMIX-1 and JMIX are spaced the larger should be FEXTRAP, values of 0.99 can be used for very close spacing. The value should be decreased for wide spacing of the grid points when there will be more decay of the non-uniformity between the grid points. 

The pitchwise average flux at JMIX is not changed by this procedure and so the uniform flow at JMIX  satisfies conservation of mass, momentum and energy between the non-uniform flow at JMIX-1  and the uniform flow at JMIX , hence it is the mixed out flow corresponding to the non-uniform flow at JMIX-1 . 

A different model is used if FEXTRAP is set to zero. In this case there is no flux extrapolation and the changes in the primary variables in the cells immediately upstream of the mixing plane are then made pitchwise uniform. Note that it is the changes not the values that are made uniform. The treatment then becomes the same as in TBLOCK-13 where it was found to be exceptionally robust. 

Flux extrapolation was found to be of little benefit and slightly destabilising on the downstream side of the mixing plane and so is not used there. Since, with flow in the positive J direction, JMIX+1 is on the mixing plane the next surface downstream of the mixing plane is JMIX+2. The cells between JMIX+1 and JMIX+2 are updated using the pitchwise uniform flux from the uniform flow at JMIX+1 and the pitchwise average flux at JMIX+2. Hence the changes that points at JMIX+2 receive from their upstream cells is pitchwise uniform. However, they also receive a pitchwise non-uniform change from the cells downstream of them so the flow on them is not pitchwise uniform. This ensures conservation of mass momentum and energy between the mixing plane and the downstream flow. This is the treatment used in TBLOCK-13, it is robust and permits reversed flow but it does tend to make the flow too uniform when applied close to a leading edge, in which case the entropy and enthalpy downstream of the mixing plane may not be pitchwise uniform. This is overcome by smoothing the flow at JMIX+2 towards an isentropic flow which is calculated using with the local static pressure at JMIX+2, the pitchwise uniform enthalpy and entropy from JMIX+1 and the flow direction from a weighted average of the pitchwise uniform value at the mixing plane and the average of the pitchwise varying values at JMIX+3  and JMIX+4 .  The fraction of the average downstream angles used is  FANGLE, which is input as data in card 19, and for which a typical value is 0.9 . Taking the average flow direction from JMIX+3  and JMIX+4 was found to be more stable and not significantly less accurate than extrapolating the flow direction from JMIX+3  and JMIX+4. On every time step the flow at JMIX+2 is smoothed towards this isentropic value by a factor RFMIX, a low value of 0.01 is usually sufficient for this, although higher values (say 0.05) are usually perfectly stable.  If RFMIX = zero then there is no smoothing to isentropic flow and the treatment is the same as in TBLOCK-13. 

This procedure works well in all cases except those when the flow relative to the downstream blade row is supersonic so that pressure waves, either expansions or shocks, run into the mixing plane from downstream. In this case the pitchwise variation in flow direction downstream of the mixing plane must be compatible with the Mach number variation, i.e. they must satisfy the Prandtl-Meyer relationship. Whenever the downstream flow is supersonic this relationship is used everywhere except at mid-pitch, where the angle is still set 

by the angle extrapolation. This allows pressure waves to intersect the mixing plane without reflection as illustrated in the Figure below. 

The smoothing of points adjacent to the mixing plane has also been changed so that it does not include values of the variables on the mixing plane, this ensures that the pitchwise uniform values on the mixing plane do not influence the rest of the flow. This smoothing is scaled by FSMTHB which is input as data and for which a typical value is 1.0, however, the exact value does not seem to have much effect on the solution. 

To use exactly the same mixing plane model as in TBLOCK-13 set both FEXTRAP and RFMIX = 0.0 

Intersection of pressure waves with the mixing plane. 

The model described also works well with reverse flow across the mixing plane as illustrated by the Figure below. 

**==> picture [273 x 147] intentionally omitted <==**

Reverse flow across the mixing plane, which is in the centre of the bulge. 

## **NOTE 18.  LOW MACH NUMBER SCHEMES** 

The “scree’ scheme works well at Mach numbers down to 0.25 but convergence becomes slower and the solutions become less smooth below this. To run at very low and incompressible Mach numbers a method based on artificial compressibility is used. 

Instead of solving the continuity equation for the density it is effectively solved for the pressure using an artificial density, ρs , as a conserved variable. This is used to calculate the pressure using 

**==> picture [174 x 26] intentionally omitted <==**

Pref is usually the inlet stagnation pressure, ρs,ref the inlet stagnation density. S is an artificial speed of sound, whose value is set in the data and is typically about twice the maximum relative velocity expected in the flow, much less than the true speed of sound. The time steps are based on this artificial speed and so can be larger than the conventional steps by a factor c/S. The changes in the artificial density are a factor (c/S)[2] greater than those of the true density and so are not so susceptible to rounding errors. 

The energy and momentum equations are solved in the usual way to obtain ρE, ρVx, ρVr and ρ rVθ. 

The true density, ρ , undergoes only small changes and is only used to obtain the velocities , V , from the mass fluxes, ρ V . Hence it can be calculated from the pressure and temperature, using the gas law, with relaxation of the changes by a factor RF_PTRU , for which a typical value is 0.01.  The true density is then used to obtain the velocity components and the internal energy. If the flow is incompressible then the constant density is used. 

The value of the artificial speed of sound is automatically updated every 5 time steps using 

**==> picture [160 x 11] intentionally omitted <==**

**==> picture [139 x 12] intentionally omitted <==**

where VMAX is the current maximum relative velocity in the flow and VS_VMAX is input as data with a typical value = 2.0. RFS has a typical value = 0.002 so that the speed is only updated over the order 1000 time steps. 

The method works down to fully incompressible flow and can be used for multistage calculations. However, the calculated efficiencies are not reliable because they use the true density changes which are very small 

## **NOTE 19 THE QUASI-3D BLADE-TO-BLADE MODEL** 

The code can be run with only two spanwise gridlines to predict the flow between two stream surfaces. With cell corner storage it is necessary to have two spanwise grid points, one on each stream surface, as illustrated in the Figure below. The coordinates of only one stream surface are input and the spacing of the stream surfaces, i.e. the stream surface thickness, is input as data. It is trivial to specify no flow through the stream surfaces but this is not sufficient to ensure that the velocity vectors follow the mean surface. It is usual to apply a body force acting perpendicular to the flow to ensure this. However, with two grid points it is possible to apply the force via a pressure difference between the two surfaces. The mid point of the two surfaces is regarded as a boundary between two half cells. Any flow crossing this boundary will cause an increase in pressure in one half cell and an equal decrease in the other half cell. This is in addition to the change in pressure calculated by the normal solution procedure which is the same on both surfaces. 

**==> picture [219 x 130] intentionally omitted <==**

The change in pressure is calculated in a time marching fashion using 

**==> picture [207 x 28] intentionally omitted <==**

The mass flux is the flow crossing the mid-surface and  c  is an estimate of the local speed of sound. This gradually builds up a pressure difference that drives the flow crossing the midsurface to zero. Since the change in pressure is equal and opposite on the two stream surfaces this does not affect the streamwise component of the pressure force applied on the flow by the surfaces. 

The blade geometry is input in the usual way but only on a single stream surface. The stream surface thickness is input separately as a table of relative thickness against fraction of meridional distance.  Only the relative thicknesses are needed, the absolute values are not used. 

The pressure changes calculated by the equation above are factored by an input variable, Q3DFORCE. The value of this does not seem to be very important, very low values, e.g. 0.1, are stable but do not make the flow follow the stream surface very closely. A value of 1.0  is standard, larger values are usually stable but offer no advantage. 

Viscous forces are retained on the blade surfaces but not on the stream surfaces so that the model gives a prediction of the blade profile loss. Run times for a single blade row are the order of 10 seconds on a single processor. 

## **NOTE 20 THE THROUGHFLOW MODEL** 

The program can run as a type of throughflow calculation if IM is set equal to 2 so that there is only a single cell in the pitchwise direction. The full 3D blade geometry must be input in the usual way. However, the number of grid points in the streamwise, J, and spanwise, K, directions can be much less than for a 3D calculation. Typically 30 points streamwise and 15 points spanwise would be sufficient. This gives run times of only a few seconds per blade row. 

As with the Q3D method (Note 19)  a mean stream surface is defined at the mid point of the blade-to-blade gap as illustrated in the Figure below. Any flow crossing this surface causes an increase in pressure on one blade surface and an equal decrease on the adjacent surface.  This builds up an approximate blade loading which is updated every time step until the flow follows the mean surface. The blade loading automatically acts perpendicular to the mean surface and so does not generate loss. The loading distribution is only a crude approximation to the true 3D loading but its overall magnitude will be compatible with the flow turning imposed by the blade. This, coupled with the use of the full 3D blade geometry makes the prediction of the effects of blade lean and sweep realistic. 

As with the Q3D model the pressure changes are scaled by a factor, Q3DFORCE, which is input as data. The exact value of this is not very important, the standard value is 1.0 but larger values are usually stable and may give faster convergence. It is also found to be very beneficial to smooth the blade surface pressures as otherwise they tend not to be smooth. The smoothing also has the benefit of reducing the blade loading at the leading edge where it can become very high due to a sudden change in flow direction. The smoothing factor, SFPBLD, and number of smoothing passes, NSFPBLD, are input as data with standard values being 0.1 and 2 respectively. It should be emphasized that this smoothing only affects the blade loading and not the average pressures acting on the flow. 

**==> picture [165 x 167] intentionally omitted <==**

As with any throughflow method it is necessary to allow for any flow deviation empirically and this is done by inputting a table of either the deviation angle or the exit flow angle against fraction of span. The deviation between the flow angle and the blade centre line angle is increased from zero at the leading edge to the specified value at the trailing edge, varying linearly with the grid J index. The deviation causes the blade force to no longer act perpendicular to the flow and so, to prevent spurious loss generation, it is resolved perpendicular to the imposed flow. 

Most throughflow programs also input the loss coefficients empirically, however, in the present code it is more convenient to maintain the shear stresses on the blade surfaces and so allow the loss to be generated automatically. Clearly the wall functions are not valid when there are only 2 grid points across the pitch but the wall function model which works by specifying the value of Yplus at the grid point on the wall generates a skin friction coefficient of   Cf  =  2/(Yplus)[2 ] . This method is used when YPLUSWALL is set to be greater than 5.0 . Inputting a value of YPLUSWALL = 20 gives a very typical value of Cf = .005, this acts on the relative velocity which is the same on both blade surfaces and so produces realistic losses. 

Tip leakage can still be modeled in this method but there is no pressure difference driving the flow across the tip gap and so the leakage flow is not deflected by the blade and is only due to the difference between the inlet flow direction and the blade surface angle, hence its magnitude and loss generation is likely to be lower than in reality. 

The flow along every stream tube is effectively one-dimensional with the local flow area being that measured normal to the mean stream surface. This means that choking occurs as in 1D nozzle, the flow will choke at the point of minimum area and only normal shock waves can be predicted in supersonic flow downstream of the throat. The method therefore cannot predict the oblique shock waves that are common in turbomachines. This limitation is common to all time-marching throughflow methods which specify the flow direction. When used on a blade row with supersonic flow within the blade to blade passage, such as a transonic fan, unrealistic shock waves and shock loss can be predicted. 



# --- END OF SOURCE: new-readin-input-data-20.9 .pdf ---



# ========================================================
# START OF SOURCE: PostPy_documentation.pdf (Category: Multall Documentation)
# ========================================================

PostPy: A Python tool to post-process _Multall_ CFD output 

## **PostPy** 

This is a code to read the _Fortran77_ unformatted outputs ‘grid_out’ and ‘flow_out’ from _Multall-Open-20.9.exe._ Then, this data is post-processed and written as several multiblock _TecPlot_ inputs called ‘ParaView_TecPlotInterpreter_blades.dat’ and ‘ParaView_TecPlotInterpreter_passages.dat’, which can be easily read by the open source code _ParraView._ The code should work with any axial machine. It has not been validated with the _mix[ed flow]_ option of _Multall_ , but if the outputs are compatible it should work or at least be easy to adjust. 

## Getting started: How to initiate a session 

The Python code is organized in a directory containing ‘ _main.py_ ’ (Which currently does not contain anything, but can be used to automate the postprocessing process), and the folder ‘Components’. Components contains: 

- __init__.py 

- _001_turbomachine_analysis.py 

- Full_machine_ploter.py 

- _002_blade_row.py 

- _003_multiblock_solution.py 

- _004_grid.py 

- _005_flow_field.py 

Each python file contains one class, correspondingly: 

- Turbomachine 

- PlotMachine 

- BladeRow 

- BlockCFD 

- Coordinates 

- FlowField 

From the user point of view, the only class you directly interact with is **Turbomachine.** As said before, it is possible to automate processes through ‘ _main.py_ ’, but the tool has been conceived as an interactive one, so it is highly recommended to use it through direct user inputs in the ‘Python Console’. To do so, just load the package and create your object: 

**==> picture [383 x 102] intentionally omitted <==**

Note that calling the class ‘ _Turbomachine()_ ’ will automatically read the _Multall_ outputs ‘ _grid_out_ ’  and ‘ _flow_out_ ’ with their default names. However, if you want to store several results in the same folder you can specify which files to use: 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

**==> picture [347 x 74] intentionally omitted <==**

This command creates an object with all the things you will need to postprocess the simulation. When you call the class it automatically reads the input data, extracts the number of rows of the machine, and generates an attribute list called ‘ _rows : list’_ containing the row objects[1] . When these _row_ objects are created with the class _BladeRow_ , they automatically scan the row to extract the passage domain and the isolated blade geometry. These are stored in the attribute objects ‘ _passage_ _original’ and ‘ _blade_ _original’, both instances of the class _BlockCFD._ When the class _BlockCFD_ is called it automatically loads the attribute objects ‘ _grid_ ’ (an instance of _Coordinates_ ) and ‘ _flow_field_ ’ (an instance of _FlowField_ ). These objects themselves compute the (x,y,z) coordinates of every point of the grid and a series of flowfield variables in every node of the grid. All of these processes are automatic and happen in less than a second! To sum up, when _Turbomachine_ is called, it returns an object such that: 

- machine = ( _Turbomachine_ ) `o` plot = ( _PlotMachine_ ) 

**==> picture [226 x 40] intentionally omitted <==**

**==> picture [109 x 10] intentionally omitted <==**

**==> picture [161 x 55] intentionally omitted <==**

The attribute object ‘ _plot_ ’ has not been introduced yet but it is convenient to show it here. This is only a basic description of the structure PostPy works with, each object has its own peculiarities. 

## Quick set up: Generate _ParaView_ input 

## Create default ParaView input 

Let’s assume you only want to see 3D plots of the flowfield. In this case you just have to load _Turbomachine_ and directly ask it to generate your .dat file calling the method 

```
machine.gen_ParaView_input()
```

> 1 Note that a stage usually has two rows, the code cannot distinguish between stages, only static or moving rows. 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

**==> picture [426 x 295] intentionally omitted <==**

Note that several things have happened now. First of all, 2 consecutive processes were triggered: the computation of the passage, and the computation of the blade. If you only want to generate one of those _ParaView_ inputs you can directly call: 

```
machine.gen_blades_ParaView()
machine.gen_passages_ParaView()
```

Note that blade generation is notably faster due to the smaller number of points (~50 times less than the passage). Another important process going on here is that the tool is generating _extra geometry_ . This is not always done, as the code checks whether that geometry already exists or not[2] . This process checks each blade row (from the attribute _machine_ . _rows[j_row]_ ) and creates several instances of the geometry and flow field. Note that 2 passages and 3 blades have been saved. These are the default settings and can be changed as follows. 

## Changing the number of instances 

Each object row = ( _BladeRow_ ) has an attribute _**N_instances**_ . This can be independently changed for every row of the machine. This same object also has the auto-computed attribute _**N_blades**_ that informs the user about the number of blades of the real machine. This last attribute shouldn’t be changed. For instance, to generate an output with 3 passages in the first row and 5 in the second one this is done: 

**==> picture [250 x 55] intentionally omitted <==**

> 2 See that when writing  the blades no geometry updates were done! 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

The geometry is only generated when required. This is an example of a script to plot a quarter of the annulus of the machine: 

```
from Components import *
```

```
machine = Turbomachine()
N_rows = machine.N_rows
```

```
factor = 0.25
for i in range(N_rows):
    machine.rows[i].N_instances = int(np.ceil(machine.rows[i].N_blades
* factor))
```

```
machine.gen_ParaView_input()
```

Conveniently, _Turbomachine_ also offers the attribute _N_rows._ These are examples of the outputs in _ParaView_ . Note that the blades also contain flow information. 

**==> picture [186 x 139] intentionally omitted <==**

**==> picture [216 x 137] intentionally omitted <==**

**==> picture [408 x 156] intentionally omitted <==**

**----- Start of picture text -----**<br>
𝑀𝑟𝑒𝑙 = 1  contour<br>**----- End of picture text -----**<br>


Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

## Using the tool to learn about a case 

_PostPy_ offers more than a direct translation to _ParaView_ . All the flow field is stored in Python variables, so it is possible to do a fair amount of postprocessing within the tool itself. 

## Full machine plots 

The more general analysis tools are in the attribute object _machine.plot._ This is an instance of the class _PlotMachine_ with the methods: 

- convergence_history(file : str (optional input) ) 

- variable_evolution_1D(variable : str, avr_type : str (optional) ) 

- variable_evolution_2D(variable : str, avr_type : str (optional) ) 

- variable_B2B(variable : str, level : float, levels : list) 

- blades_contour( normal : str, level : float ) 

- blades_grid( normal : str, level : float ) 

- passage_contour( normal : str, level : float ) 

- passage_grid( normal : str, level : float ) 

- linear_cascade_blades(level : float) 

- linear_cascade_contour(level : float) 

- linear_cascade_grid(level : float) 

## Convergence history 

It is possible to obtain the residual evolution of a run calling: 

**==> picture [203 x 66] intentionally omitted <==**

By default this function will look for the _Multall_ file ‘stage.log’, but if the residuals are stored with another name it can be passed as an input to the method. This generates the plot: 

**==> picture [269 x 170] intentionally omitted <==**

The first subplot shows the residuals as evaluated by _Multall:_ Maximum change of meridional velocity per numerical time-step, root mean square of this quantity (the actual convergence criteria) and the so-called continuity error (mass flow residual). 

The second subplot shows the grid node  where the maximum change in 𝑢𝑚 was found. This is: the most problematic node in the domain. In this case we see it is towards the suction side (high 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

I index in a compressor, check _Multall_ documentation), always in the inter-row space (medium J index, this should be correlated to the grid of the specific case), and initially at the root but then at mid-span (k index). 

The last plot simply shows the evolution of the mass flow at the inlet of the computational domain. 

## 1D fluid property plots 

Calling _machine.plot.variable_evolution_1D(‘variable’)_ takes the variable specified[3] and makes the average of it at every grid plane 𝐽= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 . These surfaces are close to planes perpendicular to the meridional line of the machine, but they are not exact in general. The 𝑥 coordinate is taken from the mid-span. By default the average is mass flow average, but there is an optional input that can take the values: 

- ‘massFlowAve’ 

- ‘areaAve’ 

The implementation of these averages is discussed below. This is an example of a 1D plot (Note that each blade row is ploted in a different color!): 

**==> picture [270 x 214] intentionally omitted <==**

## 2D fluid property pitch-wise averaged plots 

This function is very similar to the previous one. Calling _machine.plot.variable_evolution_2D(‘variable’)_ takes the variable specified[4] and makes the _pitch-wise_ average of it at every grid plane 𝐽= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 . By default the average is mass flow average, but there is an optional input that can take the values: 

- ‘massFlowAve’ 

- ‘areaAve’ 

The implementation of these averages is discussed below. This is an example of a 2D plot: 

> 3 Available varibales are stored in a dictionary and they are accessible by: _machine.rows[0].passage_original.flow_field.variables.keys()._ It is also possible to read them (or even add more!) is the source code of **_005_flow_field.py** 

> 4 IBIDEM 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

**==> picture [252 x 216] intentionally omitted <==**

## 2D blade to blade plane plots 

These plots can be obtained by using the method _object.plot.variable_B2B()_ with the compulsory inputs ‘variable’ (as before, a key in the variable dictionary), ‘k’ (The spanwise position given as a fraction of the local span) and ‘levels’, which is a list with the levels from the variable to plot. Python can be tricked to plot a single contour line at level 𝑙 by maxing 𝑙𝑒𝑣𝑒𝑙𝑠= [𝑙−𝛿, 𝑙+ 𝛿] with 𝛿≪𝑙 . This method is building upon _BlockCFD. plot_B2B_process_ method, and plots of a single passage can be done from this level with the method _BlockCFD.plot_B2B()_ taking the same arguments. In this last cases ‘levels’ is an optional input. This is an example of a blade to blade plot: 

**==> picture [275 x 242] intentionally omitted <==**

Geometry plots: Choosing ‘normal’ and ‘level’ 

These methods are those reading two inputs, the string _normal_ and the float _level._ The _normal_ input is the name of the axis perpendicular to the plot, so that ‘i’ is looking to the flow-path, ‘j’ is looking to the annulus and ‘k’ is looking through the radial direction. _level_ is a float input between 0 and 1. If it is 0 it plots the first grid surface _normal_ =1, and if it is 1 it plots _normal=N_n_ . 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

The method computes where the grid plane is and plots the closest to the level required, no grid interpolations are done. 

There are 4 methods like this, two of them plot the blade object and the other two plot the passage. Contour simply sows the boundary of the objects while grid also includes the automatically generated grid by _Multall._ All of these methods only plot 1 passage, so they are quicker than the following ones. 

**==> picture [145 x 119] intentionally omitted <==**

**==> picture [143 x 116] intentionally omitted <==**

**==> picture [138 x 113] intentionally omitted <==**

## Geometry plots: Only choosing ‘level’ 

These methods are intended to provide insight into the geometry of the full cascade. There are 3 of them: 

- linear_cascade_blades( _level_ ) 

- linear_cascade_contour( _level_ 

- linear_cascade_grid( _level_ ) 

They are plots of grid surfaces 𝑘= 𝑐𝑜𝑛𝑡𝑎𝑛𝑡 at a height determined by _level_ . Be aware that when the grid surface is far from 𝑟= 𝑐𝑜𝑛𝑡𝑎𝑛𝑡 the geometry is highly distorted. However, it is fair to assume that these grid surfaces are close to stream surfaces so this distorted view is representative of the effective geometry the flow is going through. Be aware that the horizontal coordinate is the axial distance and not the distance along the grid surface. 

**==> picture [214 x 175] intentionally omitted <==**

**==> picture [207 x 170] intentionally omitted <==**

## Detail plots and numerical values 

It is also possible to get a detailed view of the flow field in a precise axial ( 𝑗𝑔𝑟𝑖𝑑 ) position, or even the numerical value of an averaged property in a region of the grid plane. All of these actions are performed by methods living in the class _BlockCFD_ , and they can be accessed by: 

`Machine.rows[` _intNumber_ `].passage_original.` _method_ 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

## _Or_ 

`Machine.rows[` _intNumber_ `].blade_original.` _method_ 

The averages shown previously in this document are also performed by methods in this class and will be discussed in the following section. 

## Pitch-wise averaged plots 

Here we are talking about two methods: 

- plot_pitch_average(variable : str, j : float, avr_type : str (optional) ) 

- plot_pitch_average_evolution(variable : str, avr_type : str (optional) ) 

_variable_ is a string calling one of the keys of the variable dictionary stored in _self.flow_field.variables_ , and _avr_type_ is an optional input specifying the averaging procedure to use. The default is set to mass flow average, and the possible methods are: 

- ‘massFlowAve’ 

- ‘areaAve’ 

- ‘mixedOutAve’ 

Note that the last method is only available at this level and not at full scale. These two methods plot the spanwise distribution of the variable selected. The first one requires an additional input ( _j,_ float between 0 and 1) specifying the axial position of the averaging plane within the row (0 is the upstream mixing plane, 1 is the downstream mixing plane). The second method simply plots all the 𝑗= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 surfaces overlapped. A continuation a compressor rotor is shown: 

**==> picture [209 x 163] intentionally omitted <==**

**==> picture [203 x 167] intentionally omitted <==**

## 𝐶𝑝 plots and similar 

There are another two methods called: 

- plot_Cp(k : float) 

- plot_variable_on_contour(variable : str, k : float) 

That work in a very similar manner. As before, variable is a key for the variables dictionary and _k_ is a float between 0 and 1 indicating the span-wise grid surface. What these methods do is 𝑃[𝑖,  ∶,   𝑘]−𝑃[𝑖,   0,   𝑘] taking a variable (in the case of the first one 𝐶𝑝 = 𝑃𝑡[𝑖,   0,   𝑘]−𝑃[𝑖,   0,   𝑘] is computed, so 𝐶𝑝 with respect to the beginning of the domain, 𝑗= 0 ) and plotting it around the contour of the domain (so 𝑖= 0 and 𝑖= 𝑁𝑖 −1 ). Note that if this method is triggered in the blade object ( _machine.rows[].blade_original.method()_ ) it will plot 𝐶𝑝 with respect to the leading edge of the 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

blade, but if these methods are called in a passage ( _machine.rows[].passage_original.method()_ ) it will contain the evolution upstream and downstream of the blade. Plots of compressor stator blade and passage 𝐶𝑝 at 75% span[5] : 

**==> picture [213 x 151] intentionally omitted <==**

**==> picture [208 x 148] intentionally omitted <==**

## Obtaining numerical results 

Finally, all of these plotting methods are based on the averaging methods themselves. There are three of them: 

- get_area_average( _variable_ : str, _level_ : float _, i_lim_ : list, _k_lim_ : list) 

- get_mass_flow_average( _variable_ : str, _level_ : float _, i_lim_ : list, _k_lim_ : list) 

- get_mixed_out_average( _level_ : float _, i_lim_ : list, _k_lim_ : list) 

When called, all of these methods return a single float value. They only take averages in planes 𝑗= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 (perpendicular to the meridional velocity), and the inputs are as follow: 

- variable: A string with the key of the variable to average. 

- level: a float between 0 and 1 giving the axial position of the averaging plane. 

- i_lim: a 2 component list with floats between 0 and 1 indicating the fraction of pitchwise plane that is taken. For pitch-wise averages take i_lim = [0, 1]. 

- J_lim: a 2 component list with floats between 0 and 1 indicating the fraction of spanwise plane that is taken for the average. 

Note that these function allow to take an average of only a fraction of the passage. 

## Averaging methods 

This subsection introduces the implementation of the averaging procedures. All of the three averaging methods (see above) are based on the method: 

- Pre_average( _variable_ : list, _level_ : float _, i_lim_ : list, _k_lim_ : list) 

This method takes as input a **list** of strings with variable names and the same inputs as the other averaging methods. Then it returns a **list** of _numpy.ndarray_ containing the value of the selected variables in the grid nodes of the averaging plane defined by [i_lim, level, k_lim], AND the **numpy.ndarray** _dA._ This last output is basic to every averaging method as it is the “differential” area associated with each grid node in the averaging surface. 

> 5 The plots for the Blades will never close at the trailing edge. This is also seen in the ParaView files: _PostPy_ is reading the blades between the coordinates _Multall_ provides, which are the real ones, but to deal with TE separation _Multall_ computes and adds a “fairing” at the trailing edge, so the “blade” in the CFD grid seems longer than the physical one. 

Jose Luis Matabuena Sedano, 

TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

dA is computed with a dual grid obtained with the mid-points between nodes of the original grid. The image shows the original nodes in blue and the computed dual grid in red. Each original node is associated to a dual grid face: 

**==> picture [232 x 185] intentionally omitted <==**

**==> picture [190 x 149] intentionally omitted <==**

Then the area of each dual grid cell is computed as (𝐴𝑣𝑒𝑟𝑎𝑔𝑒𝑉𝑒𝑟𝑡𝑖𝑐𝑎𝑙𝐸𝑑𝑔𝑒𝑠) · (𝐴𝑣𝑒𝑟𝑎𝑔𝑒𝐻𝑜𝑟𝑖𝑧𝑜𝑛𝑡𝑎𝑙𝐸𝑑𝑔𝑒𝑠) and it is asociated to the original node. 

## Area and mass averages 

Each average procedure approximates the integrals with these areas. For area average: 

**==> picture [163 x 33] intentionally omitted <==**

And for mass flow average: 

**==> picture [247 x 32] intentionally omitted <==**

Where 𝑗 iterates over all the nodes in the averaging surface. Note that this is assuming that 𝑢𝑥 is exactly perpendicular to the 𝑗= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 grid plane, OR, that 𝑗= 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 is indeed a plane with constant angle 𝛾 with the longitudinal axis. For axial machines and the grids generated by _Multall_ this a good approximation. 

## Mixed out state average 

To get a mixed out state average the first step is to define a mixed out state. In this case, the state chosen is that one that a viscid fluid will achieve after evolving through a constant section duct with inviscid walls. In the mixed out state it is true that: 

- There are no internal stresses in the fluid: 𝑢𝑟 = 0 , 𝑢𝑚 = 𝑢𝑚0 , 𝑢𝜃 = 𝐵· 𝑟 (solid body rotation). 

- There is no heat transfer between streamlines ( 𝑇= 𝑇0 ) 

**==> picture [330 x 21] intentionally omitted <==**

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

PostPy: A Python tool to post-process _Multall_ CFD output 

The last condition is integrated to achieve the pressure distribution[6] : 

**==> picture [351 x 69] intentionally omitted <==**

𝑢[2] This is enough to obtain all the fluid properties, including total ones by using 𝑇𝑡 = 𝑇+ 2𝐶𝑝 ~~.~~ The mixed out state is defined by 4 variables: 𝑢𝑚0, 𝐵, 𝑇0 and 𝑃0 . These are obtained by imposing that the mixed out state and the real flow have some integral values in common: 

- Mass flow: ∫𝜌𝑢𝑚𝑑𝐴 is conserved 

- 1 

- `-` Total energy: 𝑚̇ ∫𝑇𝑡𝜌𝑢𝑚𝑑𝐴 is conserved 

- Axial momentum: ∫(𝑃+ 𝜌𝑢𝑚2 )𝑑𝐴 is conserved 

- Angular momentum: ∫(𝜌𝑢𝑚𝑢𝜃𝑟)𝑑𝐴 is conserved[7] 

These are 4 equations that are solved simultaneously to compute the mixed out state. The mixed out average method does not let the user select which variable to average: it always returns a list of floats containing [𝑃, 𝑃𝑡, 𝑇, 𝑇𝑡, 𝑢𝑚, 𝑢𝜃, 𝑠] in international system units. If the variable is not uniform in the mixed out state, the mass average is returned. 

## Available variables 

This last section shows where extra flow variables can be computed as well as the definition of the current ones. 

All the variables are contained in a dictionary in an object instance of the class _FlowField_ . This object is called “flow_field” and it is an attribute of the class _BlockCFD._ When the class _Flowfield_ is instanciated, it automatically triggers its method _gen_variables_ and there is where the attribute _variables = (Dictionary)_ is created. This is in the source code __005_flow_field.py_ . 

More variables can be added by the user and _PostPy_ will take care of passing them to _ParaView[8]_ , but bare in mind that more variables will increase the writing time as well as the size of the final file, and simple computations are easily done in _ParaView_ interface. 

_Multall_ output provides the following variables: 

- 𝜌 

- 𝜌𝑢𝑥 

- 𝜌𝑢𝑟 

- 𝜌𝑢𝜃 𝑢[2] 

- `-` 𝜌𝑒= 𝜌(𝐶𝑣𝑇+ 2 ) 

> 6 This derivation is valid for every Mach number. Operating with 𝐵 and 𝑟 to get the circumferential Mach 𝑃 𝐵[2] 𝑟[2] −𝑟0[2] number it is possible to reach the limit for 𝑀[2] ≪1 of 𝑃0 = 1 + 𝑅𝑔𝑇0 2 ~~,~~ which is the solution for 𝜌= 𝜌0 = 𝑅𝑃𝑔0𝑇0 = 𝑐𝑜𝑛𝑠𝑡𝑎𝑛𝑡 . 7 Al lof the previous conservation equations are based on Greitzers’ Internal Flow book, the last one is my addition to retain the angular momentum: there is no external torque applied during the mixing process. 

> 8 Avoid the names i, j, k, x, y ,z both in small and capital letters. 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 

## PostPy: A Python tool to post-process _Multall_ CFD output 

- 𝜔 [𝑟𝑎𝑑 𝑠[−1] ] 

- 𝐶𝑝 and 𝛾 

The velocities are given in the stationary frame. It is trivial to obtain the velocities dividing by 𝜌 . The velocities in the 𝑦 and 𝑧 direction are computed as 𝑢𝑦 = 𝑢𝑟 sin(𝜃) + 𝑢𝜃 cos(𝜃) and 𝑢𝑧 = 𝑢𝑟 sin(𝜃) −𝑢𝜃 cos(𝜃) where 𝜃 is a coordinate from the grid (the angle of the radial vector measured from the vertical axis z). The velocities in the relative frame are obtained by 𝑢𝜃,𝑟𝑒𝑙 = 𝑢𝜃,𝑠𝑡𝑛 −𝑟· 𝜔 , 𝑢𝑟,𝑟𝑒𝑙 = 𝑢𝑟,𝑠𝑡𝑛 and 𝑢𝑥,𝑟𝑒𝑙 = 𝑢𝑥,𝑠𝑡𝑛 and then applying the same transformation. An additional velocity (meridional) is computed as 𝑢𝑚 = √𝑢𝑟[2] + 𝑢𝑥[2] , and with this the _pitch_ angle 𝑢𝑥 of the flow is obtained as cos(𝛾) = ~~.~~ The _yaw_ angle is computed both in stationary and 𝑢𝑚 𝑢𝜃 relative frame as tan(𝜎) = ~~.~~ Lastly, the absolute ( 𝛼 ) and relative ( 𝛽 ) flow angles are computed 𝑢𝑚 𝑢𝜃,𝑠𝑡𝑛 𝑢𝜃,𝑟𝑒𝑙 as tan(𝛼) = and tan(𝛽) = ~~.~~ 𝑢𝑥 𝑢𝑥 

1 Thermodynamic properties are obtained from the internal energy: 𝑇= (𝑒−𝐸𝑘) with 𝐸𝑘 = 𝐶𝑣 12 (𝑢𝜃,𝑠𝑡𝑛2 + 𝑢𝑟 + 𝑢𝑥) the kinetic energy in the stationary frame of reference. Then the static pressure is computed as 𝑃= 𝜌𝑅𝑔𝑇 and total temperature in both stationary and relative frames of reference as 𝑇𝑡 = 𝑇+ 𝐸𝑘 with 𝐸𝑘 being the kinetic energy in the correspondent reference 𝐶𝑝 system. The rest of total properties are obtained from 𝜌𝑡 𝛾−1 = 𝑃𝑡 𝛾−1𝛾 = 𝑇𝑡 ~~.~~ Mach number is ~~(~~ 𝜌 ) ~~(~~ 𝑃 ) 𝑇 computed based on the speed of sound 𝑎= √𝛾𝑅𝑔𝑇 . Note that the static properties are independent of the reference system. 

𝑇 𝑃 The entropy is computed as 𝑠= 𝐶𝑝 ln (𝑇𝑡,𝑟𝑒𝑓 ~~)~~ −𝑅𝑔 ln (𝑃𝑡,𝑟𝑒𝑓 ~~)~~ , where the reference values are taken from the total conditions at the inlet of the machine (they are uniform). 

𝑃𝑡 𝑃 = = Lastly, the total to total ( 𝛽𝑡𝑡 ~~)~~ and total to static ( 𝛽𝑡𝑠 ~~)~~ pressure ratios are also 𝑃𝑡,𝑟𝑒𝑓 𝑃𝑡,𝑟𝑒𝑓 computed. Some geometrical variables, as 𝑟 , 𝜃 and the grid surfaces ( 𝑖, 𝑗, 𝑘 ) are also saved here because they might be useful while using _ParaView._ 

Jose Luis Matabuena Sedano, TUDelt AE4206 Turbomachinery TA during course 2022/2023 



# --- END OF SOURCE: PostPy_documentation.pdf ---



# ========================================================
# START OF SOURCE: README.pdf (Category: Multall Documentation)
# ========================================================

## **README** 

The attached folders contain the 3D MULTALL based design system. 

The system has been developed over many years, it has been run on a very large number of data sets and gives realistic results in almost all cases. However, due to the limitations of turbulence and transition modeling, CFD is not an exact science, and the author will accept no responsibility for the accuracy of the results obtained. 

**The most important component of a CFD system is the user, who must understand the physics of the flow they are trying to achieve.** 

The system consists of three linked programs. These are written in FORTRAN77 and should run on any computer with a FORTRAN compiler. The only exception is that STAGEN contains calls to the plotting package HGRAPH, which is no longer available. These calls can be removed by deleting lines 1447 to 1537  of STAGEN, the program will then run but will not plot out the blade profiles. Executable versions of STAGEN, which include the plotting, are supplied for LINUX and WINDOWS systems but they are not guaranteed to work on all systems. 

MULTALL contains calls to the timing routine MCLOCK used by the gfortran  and g77 compilers, these may produce an error on other compilers  but they can either be commented out, removed, or replaced with similar calls for the compiler being used. 

The system is described with examples of its use in the attached powerpoint presentation,  multall-design.pptx  . 

## **See the Updates file in this folder for changes since the original release.** 

## **MEANGEN** 

is a meanline program that accepts input from either the screen or from a file called **meangen.in** . Given the required basic design parameters it performs a 1D design to obtain the velocity triangles on a specified stream surface. The required flow area is calculated and used to obtain the annulus boundaries. This is done for as many stages as required. An initial guess of blade numbers and blade profiles is generated and the blades are twisted to produce a free vortex flow. The program then writes an input file called **stagen.dat** for the program STAGEN. It also writes out a file **meangen.out** , which is a copy of the input data, this can be copied to **meangen.in** , edited if required, and used as input for further runs if there are only minor changes to the design. 

A new version MEANGEN-17.4.F  was added on 3/10/2017. 

## **STAGEN** 

is a blade geometry generation and manipulation program. It takes the initial guess of blade geometry produced by MEANGEN from the file **stagen.dat** , and allows the blade sections to be refined, stacked and combined into multiple stages. The input file **stagen.dat** can also be generated manually, but this takes some time and it is usually easier to start with an initial data set from MEANGEN, even if it requires significant changes. Once a data set **stagen.dat** has been set up changes to the geometry can usually be made in a few seconds. 

The number of grid points to be used and the grid spacings are set in STAGEN as are most of the control parameters for MULTALL.  STAGEN can plot out the blade sections generated but this requires the use of the graphics package HGRAPH, which is no longer available, however, it should be easy to implement a different graphics program. Delete the relevant section of the code if a plotting package is not available. 

STAGEN writes out two input files for MULTALL, **stage_new.dat** is in the “new” format which uses all unformatted data, **stage_old.dat** is in closely the same format as used in previous versions of MULTALL and uses mainly formatted data. Either data set can be used in MULTALL depending on the setting of the file **intype** . 

## **MULTALL** 

Is a three-dimensional Navier-Stokes solver written specifically for turbomachinery.  It has been continuously developed over many years and contains options to model the most common flow features found in turbomachines. It solves for the main blade path, assuming axisymmetric annulus boundaries, and so cannot deal with split blade paths or with hub and casing cavities. Although written in cylindrical coordinates, the program can be run with effectively Cartesian grids, for cascades, or for applications other than turbomachinery, by making the radial extent of the calculated region small relative to the radius. It can also be run as a quasi-3D blade-to-blade solver or as an axisymmetric throughflow solver by using only a single cell in the spanwise or pitchwise directions. 

MULTALL reads in the data sets **stage_new.dat** or **stage_old.dat** depending on the value of the variable ANSIN, which is read from file **intype** . It solves for steady flow through multiple stages using a mixing plane model to transfer the flow between blade rows. The grids are automatically made contiguous at the mixing planes. It can predict the flow through axial, mixed or radial flow machines and predicts the machine efficiency, mass flow, pressure ratio, etc, as well as the detailed flow field. A great deal of user experience ensures that the realistic results are usually obtained. 

MULTALL is very fast relative to most CFD codes and its speed benefits greatly from using the highest possible level of compiler optimisation. 

Output files **flow_out** and **grid_out** can be used for plotting the results but these need to be interfaced to the user’s plotting system. Alternatively the supplied executable plotting programs may work. The same files can be used as restart files if starting a new calculation with no change to the grid point numbers. 

A program to convert these files to a TECPLOT input file was added on 3/10/2017, see below. 

## **CONVERTING OLD DATA SETS** 

For users of earlier versions of MULTALL, it is possible to convert old data sets for MULTALL-15  or MULTALL-14  to  MULTALL_OPEN data sets using a program  CONVERT.  This reads in a file which must be named **old_readin.dat** and writes out a file called **new_readin.dat** for input to the latest version of MULTALL. 

## **PLOTTING THE RESULTS** 

The plotting programs used by the author are all based on the HGRAPH graphics system, which is no longer available. Users should interface the output to their own plotting system. However, executable versions of the author’s plotting programs for LINUX and for WINDOWS systems are provided. They should work on 

most 64 bit systems but some calls are system dependent and so they may not work on all. **The author cannot help with sorting out problems with running the plotting programs.** 

A fortran program called  CONVERT-TO-TECPLOT.F   which converts the MULTALL output plotting files  “flow_out”  and  “grid_out”  to a file named “tecplot-input.dat”, which should be readable by the commercial plotting program TECPLOT, was added on 3/10/2017.  To run this, simply compile it, type the name of the executable and answer the questions on the screen. 

## **STARTING OFF** 

Learning to use a new CFD system can be a frustrating experience until the user becomes familiar with the many options available.  There is no substitute for actually running the programs and studying the results if one wants to understand a code. 

It is suggested that new users should first run one of the sample MULTALL data sets provided to ensure that MULTALL is working properly, all the data sets should converge. Then try running MEANGEN to design a single stage axial turbine or compressor, using screen input, the option FLO_TYP = AXI is the easiest to use. Run STAGEN on the resulting data set, **stagen.dat** , accepting the simplified blade profiles with no changes. Then run the resulting data set, **stage_new.dat ,** on MULTALL **,** remember to set file **intype** to contain the single character **“N”** if using the “new” input format **.** 

Next try editing **stagen.dat** to change the blade profiles, for example, change the blade thickness, camber line angles or restagger the blades, and re-run STAGEN then MULTALL. Next re-run MEANGEN to design a two-stage machine, or try FLO_TYP= MIX for a machine with significant radius changes, and again run the design through STAGEN and MULTALL.  You will soon become an expert. Good Luck. 

More details of the programs can be obtained from the user manuals and from ASME paper GT2017-63993 . 

John Denton.   February 2017. 



# --- END OF SOURCE: README.pdf ---



# ========================================================
# START OF SOURCE: Stagen-18.1-instructions.pdf (Category: Multall Documentation)
# ========================================================

1 

## **INSTRUCTIONS FOR PROGRAM STAGEN** 

## **Original version STAGEN-17.1  .** 

## **Latest version STAGEN-17.2 has one minor change as detailed on page 3.** 

STAGEN is a blade geometry generation package that generates a data set for the 3D, multistage, turbomachinery flow calculation program MULTALL. It is intended to be very easy to use so that once the initial data file has been generated the blade geometry can be changed and a new 3D calculation started in a matter of seconds. The program is written in FORTRAN77 and should run on any machine with a FORTRAN compiler. The only exception to this is the option to plot out the blade profiles generated. This uses the graphics program HGRAPH, which is no longer available. If the program will compile without HGRAPH then it may be run without plotting the profiles, simply answer “N” when asked if you would like to plot the blade profiles. If it will not compile without HGRAPH delete lines 1448  to  1538 of the program, the lines to be deleted are clearly marked by comment cards. It should be easily possible to replace the HGRAPH plots with a different plotting package. An executable version of STAGEN, which will plot out the blade profiles, is supplied in the folder entitled “PLOTTING PROGRAMS” but this may not work on all systems. 

The blade geometry is defined using as few parameters as possible so that changes can be made quickly and easily. The program contains many comments that may explain the use of the input variables in more detail than these instructions. 

Not all the options available in MULTALL may be set by STAGEN since, for simplicity, most parameters are set by default. Less common flow features, such as shroud leakage, coolant flows, surface roughness, bleed flows, etc, which can be computed by MULTALL, are not included and must be added to the output data set (“ **stage_new.dat”** or “ **stage_old.dat** ”) manually if required. However, it would be easy to modify STAGEN to output such features. Details of the data required are in the MULTALL manual. STAGEN will produce output files for throughflow  or for quasi-3D blade-to-blade calculations if either IM  or  KM is set equal to 2 . 

Two different data sets are written by STAGEN. One, “ **stage_new.dat** ”, is for the new free format input data used in MULTALL_OPEN if the file “intype” is set to “N”.  The other, “ **stage_old.dat** ”, is formatted data, similar to that used in older versions of MULTALL, it can be used with MULTALL_OPEN if the file “intype” is set to “O” . 

The program produces an output file for a machine with a smooth annulus with tip clearances allowed for by the pinched tip model. It can generate data sets for axial, mixed or radial flow machines. The blades are first generated in two dimensions on a plane surface and are then projected onto stream surfaces, which can be for an axial, radial or mixed flow machine. The stream surfaces need not be true stream surfaces of the flow but can be any convenient axisymmetric surface, e.g. a cylinder or a cone. When projected onto the stream surface the ‘x’ coordinate on the plane surface becomes the meridional distance and the ‘y’ coordinate on the plane surface is transformed to the cylindrical angle, θ, using 

**==> picture [82 x 38] intentionally omitted <==**

2 

so that a flat plate transforms into a log spiral. Hence, if the stream surface has a change of radius the blade shape on the developed stream surface is not exactly the same as seen on the plane surface but the loading should be similar to that of a two-dimensional blade with the original profile. 

At least two stream surfaces must be used to define a blade row but as many stream surfaces as required can be used. The first stream surface must coincide with the hub of the machine and the last must be the casing of the machine. STAGEN cannot handle the option to read in the hub and casing surfaces separately from the stream surfaces, which is available in MULTALL. 

Multiple blade rows can be generated with the limits only imposed by the dimensioning of MULTALL. 

The blade geometry and flow conditions must be provided in a data file. When the program is started the user is asked for the name of this input file with an option to select **“stagen.dat”** as a default, however any other file name can be used if required. Two output files are written for different versions of MULTALL. “ **stage_new.dat** ” is for the newer input data format used in MULTALL-OPEN  and  “ **stage_old.dat** ” is for the older input format which can also be used on MULTALL_OPEN and is almost, but not quite,  compatible with previous versions of MULTALL, e.g. MULTALL_15. In addition a file called **“out”** is written to FORTRAN unit 8.  File **“out”** is not used by the flow calculation program but contains blade coordinates and other useful information, which may be useful for finding any mistakes in the input data file. 

The names of the variables used in STAGEN are mainly the same as in MULTALL and are defined in the MULTALL user manual and so the present manual should be read in conjunction with the  MULTALL manual. However, most of the default variables are defined in the Appendix to this manual, they are also defined by comments in the code. 

In order to plot the blade profiles generated, STAGEN must be compiled and linked with the graphics library HGRAPH. If HGRAPH is not available then delete lines 1448  to 1538  of the program, it will then run but not plot out the blade profiles generated. It should be easy to change the program to use a different plotting package. Alternatively an executable version of STAGEN, which will plot out the blade profiles, is supplied in the folder entitled “PLOTTING PROGRAMS”, but this may not work on all systems. Having compiled the program, simply type the name of the executable and you will then be asked for the name of the input file, which is usually **stagen.dat** . 

Most of the control parameters of the program and the gas properties are set by defaults within the program, these are used if the input variable “IFDEF” is set to 0. However, if IFDEF is set to 1 then the values of most control parameters may be read in as part of the data set. It is usually easier to edit the program and recompile it to change the default settings rather than to make small changes to the data in the input file. 

All data input is in free format so a value **must be input for every variable** , even if it is not used. Blank lines are left in order to help the layout of the input data file and these **must** be included where indicated. 

All the input data must be in SI units.  i.e. lengths in metres, velocities in m/s, pressures in N/m[2] , temperatures in K. 

3 

## STAGEN 17.2 

STAGEN 17.2 differs from 17.1 only by reading in the gas constant and gas specific heat ratio as the first line of input data. Previously these were set by default. Old stagen data sets do not have this input and their first line of data is  Card 1A, “ IM , KM  “ , they should be corrected by adding a new first line, containing the values of the gas constant, RGAS,  and gas specific heat ratio, GAMMA, before using with STAGEN-17.2 or later. 

## STAGEN 18.1 

Stagen-18,1   differs from !7.2 only in that it includes a new option for specifying the blade camber (centre) line.  If INTYPE = 4  then this is generated by inputting a table of relative centre line curvatures together with the required leading edge and trailing edge angles.  This gives more control over the local curvatures than inputting the angle directly. The values of curvature input are only slightly smoothed so that they can still be concentrated locally. Typically the curvature should be input at 6-10 points along the centre line.  Only the relative values of curvature need be input the values are automatically scaled to fit the specified change in angle from leading to trailing edge. 

4 

## DETAILS OF THE INPUT FILE  REQUIRED BY STAGEN 

The data input is in a series of lines of data, which will be referred to as “CARDS” . Some “CARDS”  are blank lines which are just there to space out the data, but they must still be input. 

All data is in Free Format . 

On starting the program you will be asked for the name of the data input file with an option to choose “stagen.dat” as a default. 

************************************************************************* 

## CARD  1 

This is new to version 17.2 

RGAS, GAMMA 

RGAS 

The gas constant in J/kg K.  A typical value for air is 287.5 

GAMMA The gas specific heat ratio. The value for air is 1.4. 

************************************************************************* 

5 

CARD 1A IM, KM 

IM 

Is the number of grid points in the pitchwise direction. Typically  in the range 19 -> 64 . Set IM = 2 to generate a throughflow data set. 

KM Is the number of grid points in the spanwise direction. Typically  in the range 19 -> 64 . Set KM = 2 to generate a quasi-3D data set on a stream surface. ************************************************************************* 

6 

## CARD 2 FPRAT, FPMAX 

FPRAT Is the grid expansion ratio in the pitchwise direction. This should be less than 1.4. A typical value is 1.25 . 

FPMAX Is the ratio of the maximum grid spacing in the pitchwise direction to that of the first two grid points. Typically in the range  5 -> 25  . 

************************************************************************* 

CARD 3 FRRAT, FRMAX 

FRRAT Is the grid expansion ratio in the spanwise direction. Less than 1.4. Typical value = 1.25 

FRMAX Is the ratio of the maximum grid spacing in the spanwise direction to that at the first two grid points. Typically in the range 5 -> 25. 

************************************************************************* 

## CARD 3A IFDEF 

If IFDEF = 0  the default control parameters are set within the program. If IFDEF is not zero then these parameters must be read in from the next 11 cards, 3B  to 3L . 

************************************************************************* 

CARDS 3B to 3L ARE ONLY NEEDED IF “IFDEF” IS NOT ZERO SEE THE MAIN 3D PROGRAM (MULTALL) INSTRUCTIONS FOR THE MEANING OF THE PROGRAM CONTROL PARAMETERS SET BY THEM. ************************************************************************* 

7 

## CARD 3B NMAX, NCHANGE 

************************************************************************* 

## CARD 3C 

IN_VTAN, IN_PRESS, INPUT, INVR, ITIMST, ISMTH, IPOUT, INFLOW, NLOS, ILOS, IF_RESTART, IOUTST, IBOUND, ISHIFT 

************************************************************************* 

## CARD 3D IR, JR, KR, IRBB, JRBB, KRBB, NSBUP, NSBON, NSBDN, IFMIX, NEWGRID 

********************************************************************** 

## CARD 3E JTRANS, JTRANP, JTRANH, JTRANT 

********************************************************************** 

## CARD 3F 

## IF_CUSP, ICUSP, LCUSP, LCUSPUP, IFANGLES, IF_DESIGN 

********************************************************************** 

## CARD 3G 

CP, GA, CFL, SFT, SFX, FAC_4[TH] , MACHLIM 

************************************************************************* 

## CARD 3H 

DAMP, FBLK1, FBLK2, FBLK3, SFEX, CLIM, RFIN 

************************************************************************* 

## CARD 3I 

## IFMIX, RFMIX, FSMTHB, FEXTRAP, FANGLE, NEXTRAP_LE, NEXTRAP_TE 

************************************************************************* 

## CARD 3J 

FSTURB, TURBVIS_DAMP, TURBVIS_LIM, REYNO, PRANDTL, FR_VIS, FTRANS, YPLUSWALL, YPLAM, YPTURB 

************************************************************************* 

8 

## CARD 3K 

FAC_STMIX, FAC_ST0, FAC_ST1, FAC_ST2, FAC_ST3, FAC_SFVIS, FAC_VORT, FAC_PGRAD 

************************************************************************* 

## CARD 3L 

FRACPB, FRACPW, FRACPUP, FRACPIN, FRACPLE, FRACPTE, FRACPDWN 

************************************************************************* ************************************************************************* END OF NON_DEFAULT DATA INPUT FOR MAIN PROGRAM CONTROL PARAMETERS 

************************************************************************* 

9 

## CARD 4 NROWS, NOSECT 

NROWS Is the number of blade rows to be designed. 

NOSECT Is the number of blade sections to be designed per row. This must be the same for all rows. 

************************************************************************* 

CARD 5 FAC_SCALE 

FAC_SCALE  Is a scaling factor that will be used to multiply all blade coordinates. Set = 1.0 if the blade is to be generated at full scale. ************************************************************************* 

10 

## REPEAT ALL CARDS 6 TO 28 FOR EACH BLADE ROW 

CARD 6 Blank Line CARD 7 Title of the blade row, any alphanumeric characters in rows 1 to 72. 

CARD 8 Blank Line 

************************************************************************* 

## CARD 9 NINTUP, NINTON, NINTDN 

NINTUP Number of grid spacings requested upstream of the leading edge. 

NINTON Number of grid spacings requested on the blade surface. NINTDN Number of grid spacings requested downstream of the trailing edge. 

Note: These are the number of grid spacings which = number of grid points -1 

************************************************************************* 

11 

## CARDS 10 XFRAC( **I** ), RELSPCE( **I** ) 

A table of I values of the relative meridional spacings of the final grid as a function of the meridional chord. 

XFRAC(I) Fraction of meridional chord. RELSPCE(I)  Relative grid spacing at this x value. 

The table is read until a value of XFRAC(I) greater than 0.99999 is found  so the meridional chord must vary from 0.0 to 1.0. The relative spacings can be in any units as long as they are all relative not absolute values.  Typically about 5 values of XFRAC and RELSPCE are sufficient to define the final grid spacings on the blade. 

************************************************************************* 

## CARD 11 NBLADE 

NBLADE Is the number of blades in the current blade row. 

*************************************************************** 

12 

## CARD 12 RPMROW, PUPROW, PLEROW, PTEROW, PDROW 

RPMROW Is the rotational speed of the blade row. Positive if the rotation is in the theta direction. It may be negative. 

- PUPROW Is a guess of the static pressure at mid-span upstream of the blade row, in N/m[2] . 

- PLEROW Is a guess of the static pressure at mid-span at the leading edge of the blade row, in N/m[2] . 

- PTEROW Is a guess of the static pressure at mid-span at the trailing edge of the blade row, in N/m[2] . 

- PDROW Is a guess of the static pressure at mid-span at exit from the blade row, in N/m[2] . 

Note: These pressures are only used for the initial guess. They should not influence the final solution but a better guess will give faster convergence. 

*************************************************************** 

13 

## CARD 13 KTIPS, KTIPE, JROTHS, JROTHE, JROTTS, JROTTE FRACTIP, RPMHUB 

KTIPS Is the K value at which tip clearance starts. Set = 1 for hub clearance. KTIPE Is the K value at which tip clearance ends. Set = KM for tip clearance. JROTHS Is the J value at which the hub starts to rotate at RPMHUB. JROTHE Is the J value at which the hub stops rotating at RPMHUB. JROTTS Is the J value at which the casing starts rotating at RPMROW. JROTTE Is the J value at which the casing stops rotating at RPMROW. FRACTIP Is the tip or hub clearance as a fraction of the blade span. RPMHUB Is the rotational speed of the hub in between the J points JROTHS, JROTHE. in RPM . 

************************************************************************* 

Note only a singe value of tip clearance can be used. To vary the clearance from leading edge to trailing edge, edit the final data set. 

14 

REPEAT CARDS   14  TO  28  for each of the NOSECT blade sections on the current blade row. 

CARD 14 Blank line CARD 15 Title of the current blade section. Any alphanumeric characters in columns 1 to 72. 

CARD 16 Blank line 

************************************************************************* 

CARD 16A INTYPE 

INTYPE = 0. Means that the blade section is specified by a set of (x,y) coordinates going around the blade surface. These are input as data in CARD 16C. 

INTYPE =1. Means that the blade section is generated by specifying its centre line slope and a mathematically generated thickness distribution. This is the most usual type of input in versions earlier than 18.1. 

INTYPE = 2. Means that the blade section is generated by specifying its centre line slope and its tangential thickness above and below the centre line at as many points as required along the axial chord. 

INTYPE = 3.  Means that the blade is section specified by the surface slopes of its upper and lower surfaces at as many points as required along the axial chord. 

15 

- INTYPE = 4. Means that the blade section is defined by a table of relative curvatures of its centre line and a mathematically generated thickness distribution. This is now (version 18.1) considered to be the standard method for generating the blade sections. 

*********************************************************************** 

## CARD 16B THIS IS ONLY NEEDED IF INTYPE = 0 NPOINTS , NXPTS, IFCLOCK, IFREV 

- NPOINTS 

   - Is the number of points around the blade at which coordinates will be given when INTYPE = 0. 

- NXPTS Is the number of points on the camber line that will be used to generate the final blade. This should be far more than the number of grid points. Typically 200 points should be enough. 

- IFCLOCK The points to be input go clockwise round the blade if IFCLOCK = 0, anticlockwise if IFCLOCK = 1. 

IFREV The upper and lower surfaces are inverted if IFREV = 1, no changes if IFREV = 0 . *************************************************************** 

## CARD 16 C THIS IS ONLY NEEDED IF  INTYPE = 0 

A table of NPOINTS values of XIN , YIN 

XIN(N), YIN(N) The x,y coordinates of points on the blade surface. Typically 100 points are needed to define a blade accurately with close clustering around the leading and trailing edges. 

*************************************************************** 

16 

## IF INTYPE IS NOT = 0  READ IN CARDS 17- 20 . JUMP TO CARD  21 IF INTYPE = 0. 

************************************************************************ 

## CARD 17 NPIN, NXPTS, NSMOOTH 

NPIN Is the number of points in the table of camber line slopes , blade thicknesses, etc, input in the next card. Typically = 5 ->10 points are sufficient. 

NXPTS Is the number of points on the camber line that will be used to generate the blade. Typically 200 points should be enough. 

NSMOOTH Is the number of times that the input camber line slope, blade thickness or surface slope input above will be smoothed.  Typically = 2. 

- ************************************************************************* 

## IF INTYPE = 1  READ CARD 18 

## CARD 18 

## FRAC(N), SLOPE(N), N= 1, NPIN 

FRAC(N) Is the fraction of meridional chord at which the camber line slope is input. The first value must be 0.0 and the last value 1.0 . 

SLOPE(N) Is the camber line slope in degrees at FRAC(N). The slope is positive if a vector along the camber line points in (i.e. has a positive component in) the direction of rotation. 

*************************************************************** 

17 

## IF INTYPE = 2 READ CARD 18A 

## CARD 18A FRAC(N), SLOPE(N), TKH(N), TKL(N) N= 1, NPIN 

FRAC(N) Is the fraction of meridional chord at which the camber line slope is input. The first value must be 0.0 and the last value 1.0 . 

   - SLOPE(N) Is the camber line slope in degrees at FRAC(N). The slope is positive if a vector along the camber line points in (i.e. in the direction of increasing meridional distance) has a positive component in the direction of rotation. 

   - TKH(N) The blade tangential thickness above the centre line as a fraction of the meridional chord. 

   - TKL(N) The blade tangential thickness below the centre line as a fraction of the meridional chord. 

- ********************************************************************** 

18 

## IF INTYPE = 3 INPUT CARD 18B 

## CARD 18B 

FRAC(N), SLPUP(N), SLPLOW(N)  ,  N = 1, NPIN 

FRAC(N) Is the fraction of meridional chord at which the camber line slope is input. The first value must be 0.0 and the last value 1.0 . 

SLPUP(N) Is the slope of the upper blade surface in degrees. 

SLPLOW(N) Is the slope of the lower blade surface in degrees. 

Note. It is more difficult to generate a good blade shape using this method but it does give most control over the surface curvature. *************************************************************** 

19 

## IF INTYPE = 4 INPUT CARDS 18C and D 

CARD 18C SLOPE_LE, SLOPE_TE 

SLOPE_LE Is the centre line slope at the leading edge. In degrees. 

SLOPE_TE Is the centre line slope at the trailing edge. In degrees. 

*************************************************************** 

CARD 18D FRAC(N), CURV(N), N= 1, NPIN 

FRAC(N) 

Is the fraction of meridional chord at which the centre line curvature is input. The first value must be 0.0 and the last value 1.0 . 

CURV(N) 

Is the relative centre line curvature at FRAC(N). Only the relative curvature need be input. The values are scaled to make them compatible with the leading edge and trailing edge angles input in CARD 18C. 

NOTE. INTYPE = 4 is now, in version 18.1,  the preferred option for generating the blade centre line. 

*************************************************************** 

20 

CARD 19 must be input for INTYPE = 1, 2, 3 or 4 but some of the values are not used unless INTYPE = 1 or 4. 

## CARD 19 

## TKLE, TKTE, TKMAX, XTMAX, XMODLE, XMODTE, TK_TYP 

   - TKLE Is the leading edge thickness as a fraction of the blade chord. Card 20 decides which chord it is based on. 

   - TKTE Is the trailing edge thickness as a fraction of the blade chord. Card 20 decides which chord it is based on. 

   - TKMAX Is the maximum thickness (as a fraction of the blade chord) of the final blade section. Card 20 decides which chord it is based on. 

   - XTMAX Is the position of maximum thickness as a fraction of the blade axial chord. 

   - XMODLE Is the fraction of axial chord over which the leading edge will be rounded. Typically = 0.02 . 

   - XMODTE Is the fraction of the axial chord over which the trailing edge will be rounded. Typically = 0.02 . Set = 0 for a square trailing edge of thickness TKTE. 

   - TK_TYP Controls the shape of the thickness distribution.  Typically = 2.0 . Large values give a "square " thickness distribution.  A value 1.0 gives a "triangular" distribution. Non integer values may be used, e.g. TK_TYP = 1.8 is quite common. 

- *************************************************************** 

21 

## CARD 20 FCHORD, FPERP, FTKSCALE 

## FCHORD 

Determines whether the above thicknesses are fractions of the axial chord or of the true chord. FCHORD = 1 means they are fractions of the true chord. FCHORD = 0 means fractions of the axial chord. 

## FPERP 

When INTYPE = 1 this controls whether the thickness distribution is added perpendicular to the camber line or in the tangential direction . FPERP =  1 uses the perpendicular thickness and is most usual. However, for very thick and high camber blades this may cause problems and so it may be necessary to set FPERP = 0 to use a tangential thickness distribution. 

FTKSCALE Is used to decide whether to scale the 

maximum blade thickness to the value TKMAX input above. This is useful if INTYPE = 2 or 3. It is not used if INTYPE = 0. FTKSCALE = 1 means the thicknesses are scaled. FTKSCALE = 0 means the thicknesses are not scaled. 

*************************************************************** 

22 

## CARD 21 ROTN, XROT, YROT 

ROTN 

Is the angle by which the blade just generated will be rotated in the clockwise sense about the point XROT,YROT.  In degrees. 

XROT Is the X coordinate of the point about which the blade will be rotated as a fraction of the axial chord with the origin at the leading edge. 

YROT Is the Y coordinate of the point about which the blade will be rotated as a fraction of the axial chord with the origin at the leading edge. 

********************************************************************* 

## CARD 22 

## XCUP, XCDWN, BETUP, BETDN 

XCUP 

The axial extend of the grid upstream of the blade as a fraction of the axial chord. Typically = 0.5 . 

XCDWN The axial extend of the grid downstream of the blade as a fraction of the axial chord. Typically = 0.5 . 

BETUP The angle of the upstream grid extension. Usually the same as the camber line angle at the leading edge. In degrees. May be negative. 

BETDN The angle of the downstream grid extension. Usually the same as the camber line angle at the trailing edge. In degrees. May be –ve  . 

************************************************************************ 

23 

## CARD 23 BLANK CARD 

************************************************************************ 

## CARD 24 NSSURF 

NSSURF 

Is the number of points is the table of stream surface coordinates to be input in the next card. The final blade coordinates will be generated on this stream surface. The stream surface used need not be a true stream surface of the flow, any convenient axisymmetric surface (such as a conical surface) can be used. However, in many cases its coordinates may conveniently be taken from a throughflow solution. Typically about 8 points should be sufficient. 

Preferably one point should coincide with the blade row leading edge and one with the trailing edge. 

************************************************************************ 

## CARD 25 XRIN(N) ,  N = 1,NSSURF 

## XRIN(N) 

Is the axial coordinate of the N th point on the stream surface. Note the first point must be upstream of the leading edge grid point and the last point must be downstream of the trailing edge grid point on the blade section being generated. 

************************************************************************ 

24 

CARD 25a RIN(N) ,  N = 1,NSSURF 

RIN(N) Is the radius of the N th point on the stream surface. See comments on the last card. 

************************************************************************ 

## CARD 26 

## XLE, XTE, RLE, RTE 

XLE 

Is the x coordinate of the leading edge of the final blade. 

XTE 

is the x coordinate of the trailing edge of the final blade. 

RLE Is the radial coordinate of the leading edge of the final blade. 

RTE Is the radial coordinate of the trailing edge of the final blade. 

NOTE: All these points must lie on the stream surface input in the last two cards. 

************************************************************************ 

25 

## CARD 27 FCENTROID, FTANG, FLEAN, FSWEEP, FAXIAL 

These cards determine the final stacking of the section generated. 

FCENTROID  If this = 1 the blade is stacked with its centroid on a radial line through the centroid of the hub section. If FCENTROID  = 0.0 the blade is stacked on its leading edge.  FTANG, FLEAN, FSWEEP, FAXIAL will then make changes relative to this stacking. 

- FTANG 

      - The blade section is leaned in the tangential (i.e. circumferential) direction by a distance = FTANG x its meridional chord. FTANG may be positive or negative. 

   - FLEAN The blade section is leaned in the direction perpendicular to its chord line by a distance FTANG x its meridional chord. 

   - FSWEEP The blade section is swept along its chord line in the downstream direction by FSWEEP x its meridional chord. 

   - FAXIAL The blade section is moved in the axial (downstream) direction by FAXIAL x its meridional chord. 

- NOTE:   FTANG, FLEAN, FSWEEP AND FAXIAL   should all be set to zero and FCENTROID to 1 to obtain a stacking through the centroids of the blade sections. 

The stacking options cannot be used for blades where the radius change between the leading and trailing edge is larger than the axial extent of the blade. To prevent any stacking changes in this case set FCENTROID = 2.0 . 

************************************************************************ 

26 

## CARD 28 FSCALE, FCONST 

After stacking the blade can be scaled to increase it local chord. This can also be done by changing the coordinates XLE, XTE in card 26. The blade remains on the stream surface. 

FSCALE The blade meridional chord is multiplied by FSCALE. 

FCONST The scaling is done so that a point at a fraction FCONST of the meridional chord from the leading edge remains fixed. 

Note that this can be used to give local sweep to the blade, for example by keeping the trailing edge fixed and increasing the meridional chord. 

************************************************************ 

END OF DATA INPUT ON THE CURRENT BLADE SECTION RETURN TO CARD 14 TO START THE NEXT SECTION OF THE CURRENT BLADE ROW. 

************************************************************ 

************************************************************ END OF DATA INPUT ON THE CURRENT BLADE ROW RETURN TO CARD 6 TO START THE NEXT BLADE ROW, UNLESS THIS IS THE LAST ROW, IN WHICH CASE MOVE ON TO CARD 29. 

************************************************************ 

27 

## CARD  29 BLANK LINE 

************************************************************************ 

## CARD   29A 

## PUPHUB, PUPTIP, PDHUB, PDTIP 

- PUPHUB 

Is a guess of the inlet pressure on the hub at the upstream boundary of  the whole calculation, in N/m[2] . 

- PUPTIP Is a guess of the inlet pressure on the casing at the upstream boundary of the whole calculation, in N/m[2] . 

- PDHUB Is the static pressure on the hub at the downstream boundary of the whole calculation, in N/m[2] . This is a boundary condition whose use is determined by IPOUT. 

PDTIP Is the static pressure on the casing at the downstream boundary of the whole calculation, in N/m[2] . This is a boundary condition whose use is determined by IPOUT. 

************************************************************************ 

## CARD 30 BLANK CARD 

************************************************************************ 

## CARD 31 NINLET 

NINLET 

Is the number of spanwise points at which the inlet flow conditions are to be specified. Also used for the exit pressure profile if requested. 

- ************************************************************************ 

28 

## CARD 32 

FSPAN(I) I = 1,NINLET 

FSPAN(I) Is the fraction of the span at which the inlet or exit conditions are specified in the next few cards. 

************************************************************************ 

CARD 33 POIN(I) I = 1, NINLET 

POIN(I) Are the inlet stagnation pressures at the above fractions of the span. In N/m**2 

************************************************************************ 

## CARD 34 

TOIN(I) I = 1, NINLET 

TOIN(I) Are the inlet stagnation temperature, in K, at the above fractions of the span. 

************************************************************************ 

## CARD 35 

VTIN(I) I = 1, NINLET 

VTIN(I) Is the inlet swirl velocity at the above fractions of the span. In m/s . 

************************************************************************ 

## CARD 36 

VMIN(I) I = 1, NINLET 

VMIN(I) Is the inlet meridional velocity at the above fractions of the span. In m/s . 

************************************************************************ 

29 

CARD 37 B1IN(I) I = 1, NINLET 

B1IN(I) Is the inlet meridional yaw angle, Tan[-1] (Vt/Vm) , at the above fractions of the span.  Positive if the swirl is in the direction of rotation. 

************************************************************************ 

## CARD 38 

BRIN(I) I = 1, NINLET 

BRIN(I) Is the inlet meridional pitch angle , Tan[-1] (Vr/Vx) ,  at the above fractions of the span. 

************************************************************************ 

************************************************************************ ************************************************************************ 

## END OF INPUT DATA TO STAGEN 

************************************************************************ ************************************************************************ 

30 

## APPENDIX. LIST OF DEFAULT VALUES SET BY STAGEN 

These values can easily be changed by editing and recompiling the program. The meaning of the variables is also described by comments in the code. 

## INTEGER VARIABLES 

NMAX = 9000 Maximum number of time steps. IN_VTAN = 0 Inlet boundary condition for the flow angle. The absolute flow angle is fixed. IN_PRESS = 0 The pressure at the inlet boundary is calculated from the computed density. INPUT      = 2 The blade geometry is input on the hub and casing stream surfaces in addition to any other streamwise surfaces. IN_VR      = 0 The radial velocity at inlet is obtained by extrapolation from the interior flow field. ITIMST    = 3 Using the standard “scree” scheme. IPOUT = 1 Exit boundary uses fixed pressures at the hub and casing with a linear variation between. INFLOW = 0 Mass flow rate not specified. ILOS = 10 Simple mixing length turbulence model used. NLOS = 5 Viscous forces updated every 5 steps. IF_RESTART=0 Not starting from a restart file. IOUTST = 1 Writing out a restart file when finished. IBOUND = 0 Viscous shear on all solid surfaces. IR,JR,KR = 3 Cell size of the first multigrid blocks. IRBB,JRBB,KRBB =9 Cell size of the second level multigrid blocks. NSBUP = 1 One superblock upstream of the leading edge. NSBON = 2 Three superblocks in the blade row. NSBDN = 1 One superblock downstream of the trailing edge. IFMIX = 1 Standard mixing plane treatment. NEWGRID= 0 No generation of a new grid by the solver. 

31 

JTRANS, JTRANP =0 Fully turbulent boundary layers on the blades. JTRANH, JTRANT=0  Fully turbulent boundary layers on the endwalls. 

ISHIFT = 2 Grids are automatically adjusted to be contiguous at the mixing plane. NCHANGE = 1000 Smoothing and damping factors are increased over the first 1000 steps. IF_CUSP = 0 No cusp will be generated. LCUSP = 4 Length of cusp to be generated. ICUSP     = 0 Any cusp is centred on the blade centre line. LCUSPUP= 0 Cusp starts LCUSPUP points upstream of the trailing edge. IFANGLES=0 The upstream and downstream grid angles are obtained by extrapolation from the blade centre line. NEXTRAP_LE = 10 The upstream grid direction is extrapolated using the first 10 points on the blade. NEXTRAP_TE = 10 The downstream grid direction is extrapolated using the last 10 points on the blade. IF_DESIGN = 0 The blade shape will not be changed within MULTALL. IF_RESTAGGER=0 The blade witll not be restaggered within MULTALL. IF_LEAN = 0 The blade will not be leaned within MULTALL. 

## GAS PROPERTIES 

- CP = 1005. Specific heat capacity is for air at room temperatures. 

- GA = 1.4 Specific heat ratio is for air. 

## FLOATING POINT CONTROL VARIABLES 

CFL = 0.4 The time step length is set by CFL and a standard safe value is 0.4 . SFT = 0.005 The smoothing in the pitchwise and spanwise directions is the standard value, 0.005. 

32 

- SFX = 0.005 The smoothing in the streamwise (meridional) direction is the standard value, 0.005. 

- FAC_4TH = 0.8 The proportion of 4[th] order smoothing is 0.8. MACHLIM = 2 The Mach number limiter is 2.0 . DAMP = 10 The damping factor is 10, a standard value. FBLK1 = 0.4 The changes for the first level of multigrid blocks are reduced by 0.4 . 

- FBLK1 = 0.2 The changes for the second level of multigrid blocks are reduced by 0.2 . 

- FBLK3 = 0.1 The changes for the superblocks are reduced by 0.1. 

- SFEX = 0.0 No exit flow smoothing. CLIM = 0.001 Convergence limit on the percentage change in the average residuals. 

- RFIN = 0.5 Relaxation factor on the changes in inlet flow conditions. 

- RFMIX = 0.025 Relaxation factor on the isentropic forcing of the flow downstream of the mixing plane. 

- FSMTHB = 1.0 Factor for increasing the smoothing at the inlet and exit boundaries and at the mixing plane. 

- FEXTRAP = 0.8 Flux extrapolation factor at the mixing plane. Also used to extrapolate the pressure to the exit boundary. 

- FANGLE = 0.8 Angle extrapolation factor downstream of the mixing plane. 

## VISCOUS MODEL PARAMETERS 

FSTURB = 1.0 The free stream turbulent viscosity is the laminar viscosity x FSTURB . TURBVISDAMP= 0.5 The pitchwise average turbulent viscosity is halved across a mixing plane. 

- TURBVISLIM = 1000.   The maximum accepted value of turbulent viscosity = TURBVISLIM x laminar viscosity . 

33 

|REYNO = 800000.|The Reynolds number of the first blade row|
|---|---|
||based on the axial chord and the exit flow|
||velocity of the first blade row. This is used to|
||set the level of laminar viscosity.|
|PRANDTL = 1.0|The Prandtl number of the fluid, about 1.0|
||for air.|
|RF_VIS = 0.5|Changes in turbulent viscosity are relaxed by|
||0.5.|
|FTRANS = 0.001|Transition occurs whenever the ratio of|
||turbulent to laminar viscosity exceeds this|
||value.|
|YPLUSWALL = 0.0|The skin friction is calculated from the|
||specified YPLUSWALL only if YPLUSWALL is|
||greater than 5.0, otherwise use the standard|
||wall functions.|
|YPLAM  = 5.0|No turbulent viscosity is allowed for YPLUS|
||less than YPLAM .|
|YPTURB = 25.0|Turbulent viscosity is damped between|
||YPLUS = YPLAM  and YPTURB.|
|FACMIXUP = 2.0|The turbulent viscosity is increased by this|
||over the first NMIXUP steps.|
|NMIXUP = 1000|The number of time steps over which the|
||turbulent viscosity is increased.|
|FRACPB = 0.03|The mixing length limit in the blade row if|
||using ILOS = 10.|
|FRACPW = 0.03|The mixing length limit downstream of the|
||blades if using ILOS = 10.|
|FRACPUP = 0.03|The mixing length limit upstream of the|
||blades if using ILOS = 10.|
|FRACPIN = 0.02|The mixing length limit at the inlet boundary|
||if using ILOS = 100.|
|FRACPLE = 0.03|The mixing length limit at blade leading edge|
||if using ILOS = 100.|
|FRACPTE = 0.03|The mixing length limit at blade trailing edge|
||if using ILOS = 100.|
|FRACPDWN= 0.04|The mixing length limit at the downstream|
||boundary or mixing plane if using ILOS = 100.|
|FAC_STMIX = 0.0|The S-A model is used without trying to|
||match the mixing length turbulent viscosity.|



34 

FAC_ST0 = 1.0 Factor scaling the first source term in the S-A model. FAC_ST1 = 1.0 Factor scaling the second source term in the S-A model. FAC_ST2 = 1.0 Factor scaling the third source term in the S-A model. FAC_ST3 = 1.0 Factor scaling the fourth source term in the S-A model. FAC_SFVIS = 2.0 The smoothing of the turbulent viscosity calculated by the S-A model is multiplied by this factor. FAC_VORT = 0.0 The factor to increase the turbulent viscosity due to streamwise vorticity. FAC_PGRAD = 0.0 The factor to increase the turbulent viscosity due to the pressure gradient. 



# --- END OF SOURCE: Stagen-18.1-instructions.pdf ---



# ========================================================
# START OF SOURCE: updates.pdf (Category: Multall Documentation)
# ========================================================

## **UPDATES  to the MULTALL based design system.** 

21/3/2017 Add STAGEN-17.2  and MEANGEN-17.2. 

The only difference is that MEANGEN now passes the gas constant and specific heat ratio to STAGEN as its first line of data. Previously they were set in STAGEN by default. The STAGEN data sets provided have been updated to allow for this and will no longer work with STAGEN-17.1. 

26/5/2017 Add MULTALL-OPEN-17.4, STAGEN-17.3   and MEANGEN-17.3 . 

MULTALL-OPEN-17.4 has a few improvements and a few bug fixes but no change to the data input. The most noticeable change is that the smoothing and damping are increased over the first 100 time steps when starting from a restart file. Previously they were not increased at restart. Also the mass flow ratio, which is printed out every 200 steps, is now corrected to allow for shroud leakage flow so even when there is shroud leakage the flow ratio should become closely 1.0  .  In throughflow mode the incidence it decreased gradually over the first 1/3 of the grid points on the blade and the deviation is built up over the last 1/2 of the grid points on the blade. The bugs mainly involved the calculation of wall shear stress when there is surface roughness. Also the restart option could not be used when using the SA turbulence model because the turbulent viscosity was not being sent to the restart file. 

STAGEN-17.3  allows KTIPS  to be set to -1  in the input data file to request data for shrouded blades to  be added at the end of the STAGE_NEW.DAT file. However, the data must still be added manually. Also IF_CUSP_OUT can be set in the defaults to decide whether or not to ask MULTALL to generate a cusp. There is no change to the input data. 

MEANGEN-17.3  allows FLO_TYPE to be changed from AXI to MIX or vice-versa within a data set, so that part of a machine can be designed as AXI  and part as MIX. It also makes an estimate of the mid-span density to give better accuracy in evaluating the annulus area. There are no changes to the data input. 

## 15/8/2017 Add MULTALL-OPEN-17.5 

Version 17.5  has a bug fix and several additions. The bug fix is because previous versions did not always allow correctly for the relative motion of the hub or casing in unshrouded blade rows, the end wall was sometimes treated as rotating as the same speed as the blade row. This was correct in subroutine LOSS but wrong in subroutines NEW_LOSS and SPAL_LOSS.  It was done correctly in all subroutines in all versions up to MULTALL-15 but somehow got changed in MULTALL-OPEN. Copy the changes from 17.5 if using previous versions of MULTALL_OPEN. 

The first addition is to include an option to use the wall functions proposed by Shih et al in NASA/TM-1999-209398.  They suggest two terms in the wall function, one based on the velocity near the wall and the other based on the pressure gradient. The velocity term gives very similar results to the existing function in MUTALL It is used by setting YPLUSWALL to any value between  -1.0  and -10.0 . The pressure term is new and it is used in combination with the velocity term if YPLUSWALL is set to a 

value less than -10.0 . There is as yet little experience of how much difference this makes but so far it seems to have remarkable little effect. 

The second addition is to make the changes to the turbulent viscosity source term, ST0, in the Spalart-Allmaras model which were proposed by Lee, Wilson & Vahdati in ASME paper GT2017-63245. They add factors to increase the source term , ST0, when there is streamwise vorticity (helicity) and when there is an adverse pressure gradient and claim that this gives better agreement with predictions of the flow in transonic fans, especially with predictions of the stall point. 

The vorticity term is used if the value of FAC_VORT set to be greater than zero.  The maximum magnitude of the increase in set equal to FAC_VORT  and Lee et al suggest a value of  0.9191 for this. 

The pressure gradient term is not so straight-forward since the scaling factor on dimensionless pressure gradient is not given. The original Chinese paper on which the method is based uses a constant scaling factor of 10[6] , however, this makes the term depend on viscosity, which does not seem realistic. Hence it was decided to multiply the term by the Reynolds number, which gives it a reasonable value and makes it independent of viscosity. The value of the term varies inversely as the sixth power of velocity and so it is concentrated in regions where there is low velocity and an adverse pressure gradient. The term is used if FAC_PGRAD is greater than zero and its maximum magnitude is set equal to FAC_PGRAD. Lee et al suggest a value = 0.6565 for this. 

There is little experience of using these options yet but previous experience suggests that the source term in the SA model usually needs to be increased and they certainly seem to extend the operating range of axial compressors before stall. However, use of the pressure gradient term is dubious for centrifugal machines where the “centrifugal force”, which balances the pressure gradient, acts equally on the boundary layer and mainstream. 

Both FAC_VORT  and FAC_PGRAD are read in at the end of the line of data giving FAC_ST0, etc for the scaling factors on the Spalart-Allmaras terms. The default is that they are both zero. 

Two new test cases, 3stg-compr+samods-17.5.dat   and   r37+samods-17.5.dat, both of which use all the new features, are provided in the  “multall-test-cases” folder. 

## **3/10/2017** MEANGEN-17.4    and   CONVERT-TO-TECPLOT  added. 

MEANGEN-17.4 includes several new features which are described in the MEANGEN-INSTRUCTIONS  file. Because of the changes previous MEANGEN.IN data sets are not quite compatible with the new version. Several sample data sets for the new version are proved. 

CONVERT-TO-TECPLOT.F  is a fortran program which reads in the plotting files “flow_out”  and “grid_out”  written by MULTALL  and converts them to a file “tecplot-input.dat”   which can be read by the commercial plotting program TECPLOT. The number of blade passages to be plotted can be chosen and the output is much clearer if two or more passages are used, although the data file can then become quite large. 

**3/4/2018** Add   MULTALL-OPEN-18.2 

MULTALL-OPEN-18.2  has no major changes compared to version 17.5 but has a good deal of  “tidying up” and a few minor bug fixes.  The most significant changes are : 

The calculation of local mass flow rate is tidied up so that it is clear which is the blade flow and which is the total flow including leakage flows, coolant flow and bleed flows. The calculation of power when there are coolant flows has been corrected to use the correct mass flow. 

The average change in a conserved variable which is used to set the negative feedback in subroutine TSTEP was the average for the whole flow field. It was realised that for multistage machines with a very high pressure ratio the average change will vary through the machine, i.e. the changes in density and in mass flux, will tend to be proportional to the local values. This will tend to make the negative feedback more powerful in regions of high density and less powerful in regions of low density and will delay convergence. It has been modified so that the average change is evaluated for each blade row and then smoothed to prevent discontinuities in the change. This seems to be of some benefit even in cases without high pressure ratio.  It also speeds up the calculation slightly. 

The application of the limiting Mach number, MACHLIM, has been tidied up. The limiting velocity and density are based on limiting Mach number and the relative stagnation values at mid-pitch and mid-span at the leading edge of each blade row. The maximum velocity and minimum density in the blade row are then limited to these values. In most cases the limiting Mach number should be chosen so high that the limit will not be applied. 

The initial guess of tangential velocity has been changed to prevent any discontinuity at a leading edge or trailing edge. This reduces initial transients and usually improves convergence. 

A sample data set with blade cooling, cooltest-18.2.dat,  has been added. 

## **There is no change to the input data relative to version 17.5.** 

**17/5/2018** Add MULTALL-OPEN-18.3 

The only change in this version is the inclusion of a second option for specifying the cooling flows. The input variable IFCOOL can be set to be 1  or 2 . 

If  COOLIN = 1 the cooling model is the same as in previous versions using subroutine COOLIN_1 . The coolant ejection velocity is set by its Mach number, which is input as data, and is uniform over the cooling patch. 

If  IFCOOL = 2  then a new cooling subroutine, COOLIN_2,  is called. This calculates the coolant ejection velocity using the coolant stagnation pressure, which is input, and the local static pressure, and allows it to vary over the cooling patch. 

There is also a correction to a minor bug which occurred if using the surface roughness option in subroutine NEW_LOSS. 

**The data input is the same for both options and is not changed from that in previous versions** . 

## **5/07/2018** 

Add STAGEN-18.1.F 

STAGEN-18.1  contains a new option for generating the blade centre line. The centre line is defined by its leading edge and trailing edge angles and a table of values of the relative curvature of the centre line. Only the relative values of curvatures need be input the absolute value is obtained by fitting it to the leading and trailing edge angles. This gives more control over the local blade curvature and is now the preferred method for generating the centre line. This option is chosen by setting INTYPE = 4. There is no change to previous options. 

18/11/2019 Correct a bug in all version 

All versions of MULTALL_OPEN   contain a bug which prevents them working when using the variable gas properties option. It is surprising that no one has found this before. In the DO 7250 loop  in subroutine LOOP ,  TREF is set and this overwrites the value of TREF used for the variable gas properties and usually causes failure  To correct it please change the 2 or 3 occurrences of    TREF   in the DO 7250 loop   to   TREFF    , or some name similar which is not used elsewhere. 

8/1/2020 Version 19.2   .  Improved exit boundary condition 

An improved exit boundary condition is available as an option. This is based on a onedimensional method of characteristics which corrects to pitchwise average exit pressure to the specified value by a series of pressure waves. The pitchwise variation in the exit pressure is extrapolated from upstream by a fraction FP_XTRAP, typical value 0.9. It is felt that this allows less interference of the exit boundary with the upstream flow and is particularly desirable when shock waves are intersecting the downstream boundary. 

The new option is used when a new variable FRACWAVE  is input in card 23. If FRACWAVE is zero or is not included in Card 23  then the original option is used. Three new test cases using this option are added, these all named    ****-19.2.dat  . The new option is only available if using  “NEW_READIN” format for data input. 

A further change is to allow quasi-3D blade to blade calculations to be performed over several blade rows rather than a single row as previously. 

Other changes in version 19.2  are correction of a few minor bugs and general tidying 

up. 

## 25/05/2020 Version 20.6.  Inverse design mode. 

Version 20.6 is the same as 19.2 but with a major addition to allow inverse blade design when operating in the Q3D  blade-to-blade mode.  This enables blade profiles with specified surface pressures to be designed. The method and input data are described in detail in the attached file “inverse-design-mode.doc” which is in the MULTALL folder.  The calculation remains fully viscous with allowance for changes in stream tube thickness and radius. The method works for all Mach number levels but seems particularly good for transonic blades sometimes enabling them to be designed to be shock free. 

The calculation starts from a standard MULTALL input file in the  “new_readin”  format but in addition a new file named “inverse.in” must be read in giving the desired blade surface pressure distributions and various control parameters.  The method can design both the suction and pressure surfaces of a blade but this gives no control on the resulting blade thickness, which may become too thin or even negative. To overcome this an option to relax the thickness towards a specified thickness is included. If this is used then the blade pressure surface pressure distribution may differ from that specified but it will usually be very similar to it. 

A large number of test cases are supplied covering most types of turbomachine blade. 

4/12/2020 Version 20.9. Lookup table for fluid properties. 

Version 20.9 includes an option to use a lookup table for fluid properties as an alternative to the previous perfect or semi-perfect gas options. This can in principle be used with any fluid for which properties are available, however, so far it has only been used with steam. A program which will generate the required tables when linked to the COOLPROP system (www.coolprop.org) is provided,  as are tables covering the likely range of steam conditions in steam turbines. The program takes about 20% longer to run than a perfect gas calculation. Several test cases using a lookup table for steam turbines are provided. 

The program, instructions and test cases are provided in the folder “ lookup-table-option” which is in the “MULTALL” folder. 

The plotting program “plotall “  does not give accurate results when used with a lookup table solution and a modified version, “plotall-steam” , , which does give accurate results is provided. 



# --- END OF SOURCE: updates.pdf ---

