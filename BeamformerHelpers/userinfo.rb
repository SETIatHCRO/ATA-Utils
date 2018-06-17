load 'addresses.rb'

# Define an array of the beamformer numbers to use
$bfList = [1,2];

# Define the antenna pols to use
$antPolList = Array.new(2);
$antList = "3d,1h,2a,2b,2e,2j,3l,4j";
$antPolList[0] = "3dx,1hx,2ax,2bx,2ex,2jx,3lx,4jx,1hy,1jy";
$antPolList[1] = "3dx,1hx,2ax,2bx,2ex,2jx,3lx,4jx,1hy,1jy";

# Define the destination of the beamformer data
$addressList = [];
$addressList << Address.new(1, "x", "10.1.50.100", 50000);
$addressList << Address.new(1, "y", "10.1.50.100", 50001);
$addressList << Address.new(2, "x", "10.1.50.104", 50000);
$addressList << Address.new(2, "y", "10.1.50.104", 50001);
#$addressList << Address.new(3, "x", "10.1.50.108", 50000);
#$addressList << Address.new(3, "y", "10.1.50.108", 50001);
