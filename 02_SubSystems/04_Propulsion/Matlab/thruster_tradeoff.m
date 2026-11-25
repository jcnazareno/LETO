%% clear
clear;
clc;

%% declarations and dv

% dv budgets
dv_cap = 300; %m/s TLI lunar orbit capture (presumably gmat)
dv_sk = 240; %m/s station keeping

% Moon and orbital params
GM_moon = 4902.800066;
GM_earth = 398600.435436;
r_Moon = 1737.4; %km 
r_Earth = 6371; %km
d_Moon = 385000; %km
h_orbit_low = 160; %km
h_orbit_high = 7000; %km
g0 = 9.81; 

% orbiter parameters
M_orbiter_dry = 140; %kg

% Orbital energies; assume tli with Hohmann transfer from 250km LEO

e_high = -GM_moon/(2*(r_Moon + h_orbit_high));
e_hoh = -GM_moon/(2*r_Moon + h_orbit_high + h_orbit_low);
e_low = -GM_moon/(2*(r_Moon + h_orbit_low));
e_pot_high = -GM_moon/(r_Moon + h_orbit_high);
e_pot_low = -GM_moon/(r_Moon + h_orbit_low);
e_tli = -GM_earth/(r_Earth + 250 + d_Moon + r_Moon + h_orbit_high); % wrt earth

% ideal capture dv calculation; assume negligible orbiter mass

v_ap_tli = sqrt(2*(e_tli + GM_earth/(d_Moon + h_orbit_high))); %km/s
dv_cap_wk = sqrt(2*(e_high - e_pot_high)) - v_ap_tli; %km/s

% ideal transfer dv calculation; assume negligible orbiter mass

dv_ap = sqrt(2*(e_high - e_pot_high)) - sqrt(2*(e_hoh - e_pot_high)); %km/s
dv_per = sqrt(2*(e_hoh - e_pot_low)) - sqrt(2*(e_low - e_pot_low)); %km/s

dv_tot = (dv_sk + 1000 * (dv_cap_wk + dv_ap + dv_per))*1.2 %m/s 20% excess as per esa requirements

%% bipropellent MMH/Hydrazene + MON ; example MOOG DST-12

isp = 302; %s
m_thruster = 0.64; %kg
thrust = 22; %N

%% Monopropellent AF-M315E ; example GR-22

isp = 250; %s
m_thruster = 0.33; %kg
thrust = 22; %N

%% Hall effect electric Xenon ; example Astraeus
% 1000w power consumtion

isp = 1000; %s
m_thruster = 5; %kg ; estimate
thrust = 0.01; %N
M_orbiter_dry = M_orbiter_dry + 60; % account for power supply system and rcs 

% assume dv penalty of up to x2 because of long burn duration

%% Monopropellent cold gas Nitrogen ; example MOOG 058-118

isp = 57; %s
m_thruster = 0.023; %kg
thrust = 3.6; %N
%% performance calculations

T_spec = thrust/m_thruster; %N/kg
M_prop = M_orbiter_dry * exp(dv_tot/(g0*isp)) - M_orbiter_dry %kg
M_orbiter_tot = M_prop + M_orbiter_dry %kg; 2% for margin

% mass after innitial orbit insersion
M_orbiter_1 = M_orbiter_tot/(exp(dv_cap_wk/(g0*isp))); %kg

% assume worst case no station keeping required thus no prop loss; mass
% after perigee lowering
M_orbiter_2 = M_orbiter_1/(exp(dv_ap/(g0*isp))); %kg

% mass after apogee lowering/circularization
M_orbiter_3 = M_orbiter_2/(exp(dv_per/(g0*isp))); %kg

% assume T = isp*g0*mdot thus mdot = T/(isp*g0) thus burn duration 

t_burn_ins = (M_orbiter_tot - M_orbiter_1) / (thrust/(g0*isp)) %s
t_burn_ap = (M_orbiter_1 - M_orbiter_2) / (thrust/(g0*isp)) %s
t_burn_per = (M_orbiter_2 - M_orbiter_3) / (thrust/(g0*isp)) %s

% fractional burn time

T_high = (2*pi*(r_Moon + h_orbit_high))/sqrt(2*(e_high - e_pot_high));
T_low = (2*pi*(r_Moon + h_orbit_low))/sqrt(2*(e_low - e_pot_low));
t_frac_ins = t_burn_ins/T_high
t_frac_ap = t_burn_ap/T_high
t_frac_per = t_burn_per/T_low

%residual propellent mass
M_prop_res = M_orbiter_3 - M_orbiter_dry %kg

% dv = g0*isp*ln(m0/m)
% dv/(g0+isp) = ln(m0/m)
% exp(dv/g0+isp) = m+mprop/m
% m*exp(dv/(g0*isp))-m = mprop