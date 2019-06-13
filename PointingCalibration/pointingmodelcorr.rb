#! /usr/bin/env ruby
################################################################
##
##  pointingmodelcorr.rb
##
##  Pointing correction script.
##
##  Author: Jon Richards
##  Original Date: April 26, 2016
##
##
#################################################################

require 'rubygems'
require 'json'
require 'date'

$ataCmdPath = "/hcro/atasys/ata/run/";
$baseDir = ENV['COMPASSDIR'];
$PM_DEFAULT = -1;
$rackName = "fxa";
$rackName2 = "fxc";
$hookups;

$elevLimit = 40.0;
$cmdPre = "/bin/bash /hcro/atasys/ata/run/";
$antGroup = "fxa";
$gridSize = 3;
$gridStepSizeDeg = 3.0;
$freq = "1550.0"
$pamBand = ""; # Like "xband", if we ever want to set the pams for xband in the future
$maxSatsToLookAt = 1; # For testing initially set to 1 so we can tell what is happening!
$defaultPMValuesFilename = "originalPM.txt";
$debug = false;
$satName = "?";

$NO_HOOKUP_INFO = "NHI";
$ADCSTAT_ERROR = "AE";

$ANALYSYS_BAD_NUM_POINTS = 1000;
$ANALYSYS_BAD_PEAK_VALUE = 1001;
$ANALYSYS_CALC_ERROR     = 1002;
$ANALYSYS_SQRT_ERROR     = 1003;

#################################################################
###
###  Class to handle ibobs 
###
##################################################################

$NOEXIST_IBOB_NAME = "-1";

class AttempInfo

  attr_accessor :ibobName, :inputNum, :polNum, :walsh, :rack;

  def initialize(ibobName, inputNum, polNum, walsh, rack)
    @ibobName = ibobName;
    @inputNum = inputNum;
    @polNum = polNum;
    @walsh = walsh;
    @rack = rack;
  end

  def to_s()
    return "#{@ibobName}:#{@inputNum}:#{@polNum}:#{@walsh}:#{@rack}";
  end

  def exists?()
    if(ibobName.eql?($NOEXIST_IBOB_NAME))
      return false;
    else
      return true;
    end
  end

end

class AntAttemp

  attr_accessor :antName, :pols;

  def initialize(antName)
    @antName = antName;
    @pols = Hash.new();
  end

  def add(polName, polNum, ibobName, inputNum, walsh, rack)
    @pols[polName] = AttempInfo.new(ibobName, inputNum, polNum, walsh, rack);
  end

  def get(polName)
    return @pols[polName];
  end 

  def to_s()
    s = @antName;
    @pols.each do |k, v|
      s += "\n" + k + ":" + v.to_s;
    end
    return s;
  end

end

############################
# Class to manage one iBob
############################
class IBOB

  def initialize(name)
  end

end

# ######################################
# Class to manage all the IBOB Racks.
# BF is not done yet - they are "nil".
# ######################################
class IBOBRACK

  attr_accessor :racks;

  def initialize()
    @racks = Hash.new();
    @racks["fxa"] = readHookups("fx64a");
    @racks["fxc"] = readHookups("fx64c");
    @racks["bfa"] = nil;
    @racks["bfb"] = nil;

  end

  # fxconf.rb hookup_tab fx64c
  # : fx64c :  0 : i01.fxc:in0 : 1axc1 :  1X : Walsh 1 :
  # : fx64c :  1 : i01.fxc:in1 : 1bxc1 :  2X : Walsh 3 :
  # : fx64c :  2 : i01.fxc:in2 : 1cxc1 :  3X : Walsh 5 :
  def readHookups(rack)
    info = Hash.new();
    result = `/home/obs/ruby/bin/fxconf.rb hookup_tab #{rack}`;
    result.each do |line|
      if(line == nil || line.length < 10) then next end;
      #puts line.chomp!;
      parts = line.split(/\s+/);
      ibobName = parts[5].split(".")[0];
      antName = parts[7][0..1];
      polName = parts[7][2..2];
      inputNum = parts[5].split(".")[1].split(":")[1][-1,1];
      walsh = parts[12];
      polNum = parts[3];
      #puts ibobName + "," + antName + "," + polName + "," + inputNum;

      antAttemp = info[antName];
      if(antAttemp == nil) 
        antAttemp = AntAttemp.new(antName);
        info[antName] = antAttemp;
      end

      antAttemp.add(polName, polNum, ibobName, inputNum, walsh, rack);

    end
    return info;
  end

  def to_s(rackName)

    rack = @racks[rackName];
    if(rack == nil) then return "Rack #{rackName} not defined" end

    s = rackName;
    rack.each do |k, v|
      s += "\n" + v.to_s();
    end

    return s;

  end

  def getiBobNameAndInput(rackName, antName, pol)

    rack = @racks[rackName];
    if(rack[antName] == nil) 
      antAttemp = AntAttemp.new(antName);
      antAttemp.add(pol, "-1", $NOEXIST_IBOB_NAME, "-1","-1", rack);
      return antAttemp.get(pol);
    end
    return rack[antName].get(pol);

  end

end

# USAGE example and test...
=begin
ibobs = IBOBRACK.new();
puts ibobs.to_s("fxc");
info = ibobs.getiBobNameAndInput("fxa", '1a', "y");
puts info;
puts info.exists?();
info = ibobs.getiBobNameAndInput("fxc", '1a', "y");
if(info.exists?())
  puts info;
end
info = ibobs.getiBobNameAndInput("fxa", '1g', "x");
puts info.ibobName + ":" + info.inputNum + ":" + info.walsh;
info = ibobs.getiBobNameAndInput("fxc", '1g', "x");
puts info.ibobName + ":" + info.inputNum + ":" + info.walsh;
info = ibobs.getiBobNameAndInput("fxc", '1g', "y");
puts info.ibobName + ":" + info.inputNum + ":" + info.walsh;
=end


#################################################
# Class to hold information about one satellite.
#################################################
class Sat

  attr_accessor :name, :az, :el;

  def initialize(name, az, el)
    @name = name;
    @az = az;
    @el = el;
  end

  def to_s
    return @name + "," + @az + "," + @el;
  end

end

#########################################
# Class to handle pointing model offsets
#########################################
class PM

  attr_accessor :az, :el;

  def initialize(az, el)
    @az = az.to_s;
    @el = el.to_s;
  end

  def to_s()
    return @az + "," + @el;
  end

  def get()
    return { "az" => @az, "el" => @el };
  end

end

#######################################
# Class to manage all the antennas
#######################################
class Ants

  attr_accessor :ants, :measurements;

  def initialize(groupName)

    result = `/home/obs/ruby/bin/fxconf.rb sals`

    @ants = [];
    @measurements = Hash.new();

    # Get the antennas in the "groupName" group
    result.each do |line|         
      line = line.chomp.strip;                                     
      if(line.include?(groupName) == true)                                        
        parts = line.chomp.split(/\s+/);
        parts[1..-1].each do |a|
          #next if(!a.eql?("2a")) 
          ant = Ant.new(a);
          # Only use antennas that have a valid hookup. If an attemp 
          # input number < 0 then no hookup info has been found.
          if(ant.hookupExists?() &&
             !ant.getRMS("x").eql?($ADCSTAT_ERROR) &&
             !ant.getRMS("y").eql?($ADCSTAT_ERROR))
            @ants << Ant.new(a);
          else
            puts "No hookup info found for #{a}, removing from list.";
          end
        end
      end
    end                                                                                                                                              
  end

  def add(antName)
    @ants << Ant.name(antName);
  end

  def getAntList(separator)
    s = "";
    @ants.each do |a|
      s += a.name + separator;
    end
    return s.chop;
  end

  def track(targetName)
    cmd = "#{$cmdPre}atatrackephem \"" + getAntList(",") + " " + targetName + ".ephem -w\"";
    puts cmd;
    doCmd(cmd);
  end

  def lna()
    cmd = "#{$cmdPre}atalnaon \"" + getAntList(",") + "\"";
    doCmd(cmd);
  end

  def pams(band)
    cmd = "#{$cmdPre}atasetpams \"" + getAntList(",") + " #{band}\"";
    doCmd(cmd);
  end

  def focus(freq)
    cmd = "#{$cmdPre}atasetfocus \"" + getAntList(",") + " " + freq.to_s + "\"";
    doCmd(cmd);
  end

  def setLO(lo, freq)
    cmd = "atasetlo \"" + lo + " " +  (freq.to_f + 15529.145600).to_s + "\"";
    doCmd(cmd);
    cmd = "atasetskyfreq \"" + lo + " " + freq.to_s + "\"";
    doCmd(cmd);
  end


  def autoatten()
    $stderr.puts "Running autoattenall to set RMS=13";
    puts "Running autoattenall to set RMS=13";
    cmd = "/home/obs/bin/autoattenall.sh fx64a:fxa & /home/obs/bin/autoattenall.sh fx64c:fxa";
    doCmd(cmd);
    $stderr.puts "autoattenall finished";
    puts "autoattenall finished";
  end

  def moveAnts(from, to)
    cmd = "/home/obs/ruby/bin/fxconf.rb sagive " + from + " " + to + " " + getAntList(",");
    doCmd(cmd);

  end

  # Perform all the necessary initialization necessary before and observing.
  # # This includes tracking on the object.
  def initAnts(targetName, freq)
    $stderr.puts "Initializing antennas for target=#{targetName}, freq=#{freq}";
    puts "Initializing antennas for target=#{targetName}, freq=#{freq}";

    @targetName = targetName;

    puts getAntList(",");
    lna();
    pams($pamBand);
    focus(freq);
    setLO("b", freq);
    setLO("c", freq);
    createEphem(targetName);
    track(@targetName);
    autoatten();

    $stderr.puts "Finished Initializing antennas for target=#{targetName}, freq=#{freq}";
    puts "Finished Initializing antennas for target=#{targetName}, freq=#{freq}";
  end

  def pnOffsetAnts(azOffset, elOffset)

  end

  # Perform the measurement gathering.
  def performMeasurements()

    # Define the grid offsets
    grid = [];
    delta = (3.5/$freq.to_f * 1000.0)/2.0;
    max_deviation = delta * 4.0;

    pos = [];
    pos << 0.0;
    pos << max_deviation;
    grid << pos;

    pos = [];
    pos << 0.0;
    pos << delta;
    grid << pos;

    pos = [];
    pos << 0.0;
    pos << 0.0;
    grid << pos;

    pos = [];
    pos << 0.0;
    pos << -delta;
    grid << pos;

    pos = [];
    pos << 0.0;
    pos << -max_deviation;
    grid << pos;

    pos = [];
    pos << -max_deviation;
    pos << 0.0;
    grid << pos;

    pos = [];
    pos << -delta;
    pos << 0.0;
    grid << pos;

    pos = [];
    pos << 0.0;
    pos << 0.0;
    grid << pos;

    pos = [];
    pos << delta;
    pos << 0.0;
    grid << pos;

    pos = [];
    pos << max_deviation;
    pos << 0.0;
    grid << pos;

    puts "[start]";
    puts "Performing measurements for antennas #{getAntList(',')}";

    # Initialize the hashmap of all the measurements.
    @ants.each do |a|
      @measurements[a.name] = [];
    end

    # First, perform the measurement for the detault offsets
    # Should already be tracking
    t = Time.new.localtime
    timeString =  "Current Time : " + t.to_s
    `sleep 10`;

    puts "Getting default center measurements";
    @ants.each do |a|
      meas = Measurement.new(a.pmDefault);
      `sleep 12`;
      meas.setPwr("x", a.getPwrAvg("x").split(/\s+/)[2]);
      meas.setPwr("y", a.getPwrAvg("y").split(/\s+/)[2]);
      @measurements[a.name] << meas;

      begin
        file = File.open($defaultPMValuesFilename, "a+");
        if(timeString != nil)
          file.write(timeString + "\n");
          timeString = nil;
        end
        file.write(a.name + "," + meas.to_s + "\n") ;
      rescue IOError => e
        $stderr.puts "Trouble saving default PM values: " + e.to_s;
        exit(1);
      ensure
        file.close unless file.nil?
      end
    end

    # For testing, stop here and make sure the default PM values
    # were written to the file.
    #exit(0);

    # Offset the PM for each grid position, then get the power for that
    # position.
    grid.each_with_index do |g, i|
      x = g[0];
      y = g[1];
      puts "\nGrid position #{(i+1).to_s}, Offsetting PM #{g[0]},#{g[1]}\n";
      @ants.each do |a|
        a.offsetPm(x, y);
      end
      puts "Tracking #{@targetName}";
      track(@targetName);
      `sleep 5`;
      @ants.each do |a|
        #Commented out for testin
        meas = Measurement.new(a.offsetPM);
        `sleep 12`;
        meas.setPwr("x", a.getPwrAvg("x").split(/\s+/)[2]);
        meas.setPwr("y", a.getPwrAvg("y").split(/\s+/)[2]);
        @measurements[a.name] << meas;
      end
    end

    # Set PM back to default
    @ants.each do |a|
      a.offsetPm(0.0, 0.0);
    end


    puts "Finished measurements for antennas #{getAntList(',')}";
    puts "[end]";


    @ants.each do |a|
      # Get the Az/El of the antenna for reporting purposes
      azel = getAzEl(a.name);

      offsets_xy = Measurement.calcOffset(a.name, "xy", @measurements[a.name]);
      offsets_x  = Measurement.calcOffset(a.name, "x", @measurements[a.name]);
      offsets_y  = Measurement.calcOffset(a.name, "y", @measurements[a.name]);
      time1 = Time.new.localtime.to_s
      #1a,
      #Tue Jul 19 10:47:38 -0700 2016,
      #GPS-BIIR-11--PRN-19-,
      #205.643,59.481,
      #290.7950,77.7110,290.773043159548,77.3966612701321,0.0219568404518782,0.314338729867927
      #offset.az, offset.el, o2, o1, (o2.to_f - offset.az.to_f).abs(), (o1.to_f - offset.el.to_f).abs() 
      str = a.name + "," + time1 + "," + $satName + "," +  azel[0] + "," + azel[1] + "," + 
        offsets_xy[0].to_s + "," + 
        offsets_xy[1].to_s + "," + 
        offsets_xy[2].to_s + "," + 
        offsets_xy[3].to_s + "," + 
        offsets_xy[4].to_s + "," + 
        offsets_xy[5].to_s;
      fname = a.name + ".pnt";
      File.open(fname, 'a+') {|f| f.write(str + "\n") }

      str2 = a.name + "\n";
      @measurements[a.name].each do |m|
        str2 = str2 +  m.to_s + "\n";
      end
      str2 = str2 + str + "\n";
      File.open("allants.pnt", 'a+') {|f| f.write(str2 + "\n") }

      time1 = Time.new.localtime

      # Output the results to "corr.pnt"

      str3 = "\nant: " + a.name; 
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Date:     " + time1.to_s;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Sat:      " + $satName; 

      puts "  Elev X:   " + Measurement.getMeasString("el", "x", @measurements[a.name]);
      puts "  Elev Y:   " + Measurement.getMeasString("el", "y", @measurements[a.name]);
      puts "  Az X:     " + Measurement.getMeasString("az", "x", @measurements[a.name]);
      puts "  Az Y:     " + Measurement.getMeasString("az", "y", @measurements[a.name]);
      File.open("corr.pnt", 'a+') {|f| f.write("  Elev X:   " + 
        Measurement.getMeasString("el", "x", @measurements[a.name]) + "\n") }
      File.open("corr.pnt", 'a+') {|f| f.write("  Elev Y:   " + 
        Measurement.getMeasString("el", "y", @measurements[a.name]) + "\n") }
      File.open("corr.pnt", 'a+') {|f| f.write("  Az X:     " + 
        Measurement.getMeasString("az", "x", @measurements[a.name]) + "\n") }
      File.open("corr.pnt", 'a+') {|f| f.write("  Az Y:     " + 
        Measurement.getMeasString("az", "y", @measurements[a.name]) + "\n") }

      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Az/El:    " + azel[0].to_s + " " + azel[1].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Orig:     " + offsets_xy[0].to_s + " " + offsets_xy[1].to_s; 
      puts str3;
      str3 = "            atasetpmoffsets --absolute #{a.name} #{offsets_xy[0].to_s} #{offsets_xy[1].to_s}"; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n\n") }
      str3 = "  XY New:   " + offsets_xy[2].to_s + " " + offsets_xy[3].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  XY Diff:  " + offsets_xy[4].to_s + " " + offsets_xy[5].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Cmd:      atasetpmoffsets --absolute #{a.name} #{offsets_xy[2].to_s} #{offsets_xy[3].to_s}"; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }

      str3 = "  X New:    " + offsets_x[2].to_s + " " + offsets_x[3].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  X Diff:   " + offsets_x[4].to_s + " " + offsets_x[5].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Cmd:      atasetpmoffsets --absolute #{a.name} #{offsets_x[2].to_s} #{offsets_x[3].to_s}"; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }

      str3 = "  Y New:    " + offsets_y[2].to_s + " " + offsets_y[3].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Y Diff:   " + offsets_y[4].to_s + " " + offsets_y[5].to_s; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }
      str3 = "  Cmd:      atasetpmoffsets --absolute #{a.name} #{offsets_y[2].to_s} #{offsets_y[3].to_s}"; 
      puts str3;
      File.open("corr.pnt", 'a+') {|f| f.write(str3 + "\n") }

    end
  end


end

class Measurement

  attr_accessor :offset,:pwr;

  def initialize(offset)
    @offset = offset;
    @pwr = Hash.new();
  end

  def setPwr(pol, pwr)
    $stderr.puts "PWR: " + pol + "=" + pwr;
    @pwr[pol] = pwr;
  end

  def getPwr(pol)
    return @pwr[pol];
  end

  def getReading(pol)
    if(pol.eql?("x"))
      @pwr["x"].to_f;
    elsif(pol.eql?("y"))
      @pwr["y"].to_f;
    else
      return Math.sqrt(@pwr["x"].to_f * @pwr["x"].to_f + @pwr["y"].to_f * @pwr["y"].to_f)
    end
  end

  def getOffset(az_or_el)
    if(az_or_el.eql?("az"))
      return @offset.az;
    else
      return @offset.el;
    end
  end

  def to_s
    pwr = Math.sqrt(@pwr["x"].to_f * @pwr["x"].to_f + @pwr["y"].to_f * @pwr["y"].to_f).to_i.to_s;
    return "#{to_ff(@offset.az)}\t#{to_ff(@offset.el)}\t#{@pwr["x"].to_i.to_s}\t#{@pwr["y"].to_i.to_s}\t#{to_ff(pwr)}";
  end

  def to_ff(num)
    f = num.to_f;
    return "%.02f" % f;
  end

  def get
    pwr = Math.sqrt(@pwr["x"].to_f * @pwr["x"].to_f + @pwr["y"].to_f * @pwr["y"].to_f).to_i.to_s;
    return { "azOffset" => @offset.az, "elOffset" => @offset.el,
             "xpwr" => @pwr["x"].to_i.to_s, "ypwr" => @pwr["y"].to_i.to_s, "pwr" => pwr };
  end

  def self.calcOffset(antName, pol, measurements)
    #get the default offset
    offset = measurements[0].offset;
    pos = [];
    vals = [];
    measurements.each_with_index do |m, i|
      # Skip the first measurement, this is the center point measured at the beginning
      if(i > 0 && i < 6)
        pos << m.getOffset("el").to_f;
        vals << m.getReading(pol).to_f;
      end
    end
    #pos.each do |p| 
    #  puts p.to_s;
    #end
    #vals.each do |v| 
    #  puts v.to_s;
    #end
    o1 = analyzeFivePoint(antName, pos, vals);

    pos = [];
    vals = [];
    measurements.each_with_index do |m, i|
      if(i > 5 && i < 11)
        pos << m.getOffset("az").to_f;
        vals << m.getReading(pol).to_f;
      end
    end
    #pos.each do |p| 
    #  puts p.to_s;
    #end
    #vals.each do |v| 
    #  puts v.to_s;
    #end

    o2 = analyzeFivePoint(antName, pos, vals);
    return [offset.az, offset.el, o2, o1, (o2.to_f - offset.az.to_f).abs(), (o1.to_f - offset.el.to_f).abs() ];
  end

  def self.getMeasString(azorel, pol, measurements)
    str = "";
    if(azorel.eql?("az"))
      measurements.each_with_index do |m, i|
        if(i > 5 && i < 11)
          if(i == 8) 
            str = str + "[" + m.getReading(pol).to_s + "], ";
          else 
            str = str + m.getReading(pol).to_s + ", ";
          end
        end
      end
      return str.chop.chop;
    elsif(azorel.eql?("el"))
      measurements.each_with_index do |m, i|
        if(i > 0 && i < 6)
          if(i == 3) 
            str = str + "[" + m.getReading(pol).to_s + "], ";
          else 
            str = str + m.getReading(pol).to_s + ", ";
          end
        end
      end
      return str.chop.chop;
    end
  end

end

###############################################
# Class to hold information about one antenna
###############################################
class Ant

  attr_accessor :name, :rackName, :pmDefault, :offsetPM;

  def initialize(name)

    @name = name;

    # Get and store the pm default offsets
    ## Commented out for testing
    cmd = $cmdPre + "atagetpmoffsets " + @name;
    parts = doCmd(cmd).split(/\s+/);
    @pmDefault = PM.new(parts[1], parts[2]);

    @rackName = $rackName;

    @xHookup = $hookups.getiBobNameAndInput(@rackName, name, "x");
    if(!@xHookup.exists?())
      @rackName = $rackName2;
      @xHookup = $hookups.getiBobNameAndInput(@rackName, name, "x");
    end
    #puts "INPUT num = " + getInput("x");
    @yHookup = $hookups.getiBobNameAndInput(@rackName, name, "y");
  end

  def hookupExists?()
    if(!@xHookup.exists?() || !@yHookup.exists?())
      return false;
    end
    return true;
  end

  def getInput(pol)
    if(pol.downcase.eql?("x"))
      return @xHookup.inputNum;
    else
      return @yHookup.inputNum;
    end
  end

  def getiBobName(pol)
    if(pol.downcase.eql?("x"))
      return @xHookup.ibobName;
    else
      return @yHookup.ibobName;
    end
  end

  def getRack(pol)
    if(pol.downcase.eql?("x"))
      return @xHookup.rack;
    else
      return @yHookup.rack;
    end
  end

  def getPolNum(pol)
    if(pol.downcase.eql?("x"))
      return @xHookup.polNum;
    else
      return @yHookup.polNum;
    end
  end

  # Determine the absolute pm with an offset
  def getPmAbsoluteForOffset(azOffset, elOffset)
    return PM.new(@pmDefault.az.to_f + azOffset.to_f , @pmDefault.el.to_f + elOffset.to_f);
  end

  # Actually offset the PM
  def offsetPm(azOffset, elOffset)
    offsetPM = getPmAbsoluteForOffset(azOffset, elOffset);
    # Comment out the next 2 lines for testing without actually offsetting
    cmd = "#{$cmdPre}atasetpmoffsets --absolute " + @name + " " + offsetPM.az.to_s + " " + offsetPM.el.to_s ;
    result = doCmd(cmd);
    @offsetPM = offsetPM;
  end

  # Leave code here incase want to use it in the future.
  # Also, this code is used by the Ant class to check that the hookup 
  # exists and we have a chance of getting good readings.
  # Gets the RMS for the attemplifier
  def getRMS(pol)
    ibobName = getiBobName(pol);
    if(ibobName.length == 0)
      return $NO_HOOKUP_INFO;
    end
    input = getInput(pol).to_i;
    #puts "INPUT: " +input.to_s;
    cmd = "adcstats.rb #{ibobName}.#{@rackName}";
    result = doCmd(cmd);
    lineCount = 0;
    result.each do |line|
      parts = line.split(/\s+/);
      inx = parts[0];
      if((lineCount > 0) && inx.to_i == input)
        return parts[3];
      end
      lineCount = lineCount + 1;
    end

    return $ADCSTAT_ERROR;
  end

  def getPwrAvg(pol)
    polNum = getPolNum(pol);
    rack = getRack(pol);
    if(rack.eql?("fx64a"))
      rack = "fx64a";
    else
      rack = "fx64c";
    end
    if(rack.include?("a"))
      cmd = "ssh x1.fxa ./fxmax.rb #{rack} #{polNum} #{polNum}";
    else
      cmd = "ssh x1.fxc ./fxmax.rb #{rack} #{polNum} #{polNum}";
    end
    result = doCmd(cmd);
    puts cmd;
    return result.chomp;
  end

  def to_s()
    return @name + "," + @pmDefault.to_s;
  end

end

def getSatsUp()

  satlist = [];

  cmd = $cmdPre + "atalistsats -l gps";
  cmdResult = doCmd(cmd);
  #1  GPS-BIIF-1---PRN-25-  225.8063  -66.1573
  #2  GPS-BIIF-10--PRN-08-   47.0601  26.1785
  #3  GPS-BIIF-11--PRN-10-   24.4227  -23.9827
  cmdResult.each_line do |line|
    parts = line.strip.split(/\s+/);
    el =  parts[3];
    if(el.to_f > $elevLimit && (el.to_f < ($elevLimit + 20)))
      satlist << Sat.new(parts[1], parts[2], parts[3]);
    end
  end

  return satlist;

end

def getSatBestRising()

  satlist = Hash.new();
  satlist2 = Hash.new();
  lowestSatname = "";

  cmd = $cmdPre + "atalistsats -l gps";
  (0..1).each do |i|
    puts cmd;
    cmdResult = `#{cmd;}`
    cmdResult.each_line do |line|
      parts = line.strip.split(/\s+/);
      el =  parts[3];
      if(el.to_f < 40.0) then next; end
      if(el.to_f > 55.0) then next; end
      if(i == 0)
        satlist[parts[1]] = el;
      else
        if(satlist[parts[1]] == nil) then next; end
        if(el.to_f > satlist[parts[1]].to_f)
          satlist2[parts[1]] = el;
        end
      end
    end
    if(i == 0) then `sleep 2`;end
  end

  lowestel = 90.0;
  satlist2.each do |k,v|
    if(v.to_f < lowestel)
      lowestel = v.to_f;
      lowestSatname = k;
    end
  end

  #return [lowestSatname, lowestel];
  return lowestSatname;

end


########################################################
# Get a list of all the antennas in fxconp group "none"
########################################################
def getAnts(groupName)

  result = `/home/obs/ruby/bin/fxconf.rb sals`

  list = [];

  # Get the antennas in the "groupName" group
  result.each do |line|         
    line = line.chomp.strip;                                     
    if(line.include?(groupName) == true)                                        
      parts = line.chomp.split(/\s+/);
      parts[1..-1].each do |a|
        list << Ant.new(a);
      end
    end
  end                                                                                                                                              
  return list;                                                                                           
end

##################################################
# Create the ephemeris for a target and wrap it.
##################################################
def createEphem(targetName)

  cmd = "#{$cmdPre}ataephem " + targetName;
  doCmd(cmd);
  cmd = "#{$cmdPre}atawrapephem " + targetName + ".ephem";
  doCmd(cmd);

  return targetName + ".ephem"

end

# Get the Az/El of an antenna
def getAzEl(ant)
  cmd = "#{$cmdPre}atagetazel #{ant}";
  result = `#{cmd}`.split(/\s+/);
  return [result[1], result[2]];
end

###############################################################
#
#  analyzeFivePoint
#
#  Given 5 points and their measured power caclutate the max
#  location.
#
#  Author: Jon Richards, derived from Gerry Harp's analyzeFivePoint
#          Java method.
#  Original Date: June 29, 2016
#
#  return 
#
#################################################################

def analyzeFivePoint(antName, x, y)

  begin
    # error check
    if (x.length != 5 || y.length != 5) then return $ANALYSYS_BAD_NUM_POINTS; end

    # firstly, subtrack off background and constant offset
    back = (y[0] + y[4])/2.0;
    offset = x[2];
    xminus = x[1] - offset;
    xpeak  = x[2] - offset;
    xplus  = x[3] - offset;
    yminus = y[1] - back;
    ypeak  = y[2] - back;
    yplus  = y[3] - back;

    if(ypeak <= 0.0) then return $ANALYSYS_BAD_PEAK_VALUE; end

    # calculate the exponential alpha from the angular full width at half max
    delta1 = (xplus - xminus)/2.0;
    alpha = delta1.abs() / Math.sqrt(Math.log(2.0));
    alpha2 = alpha*alpha;

    # calculate first-order offset
    delta2 = alpha2 * Math.log(yplus / yminus) / (4.0 * delta1);
    a = ypeak / Math.exp(-delta2*delta2 / alpha2);
    dd = delta1 - delta2;
    #puts dd.to_s + "," + a.to_s + "," + yplus.to_s ;
    new_alpha = Math.sqrt(dd * dd / Math.log(a / yplus) * Math.log(2.0));

    # last error check
    if ((delta2).abs() > (2*delta1).abs()) then return $ANALYSYS_CALC_ERROR; end

    return delta2 + offset;

  rescue
    puts "SQRT ERROR!";
    File.open("allants.pnt", 'a+') {|f| f.write(antName + ", Error in analyzeFivePoint\n") }
    return $ANALYSYS_SQRT_ERROR;
  end

end

###################
# Run a command.
###################
def doCmd(cmd)
  if($debug == true)
    $stderr.puts cmd;
    puts cmd;
  end
  return `#{cmd}`;
end

def printHelp()
  puts "";
  puts "Syntax: pointingmodelcorr.rb <ant list, comma separated>";
  puts " Example: pointingmodelcorr.rb 1a,1b,1c";
  puts "";
  puts "Output: A file named \"corr.pnt\" contains as an example:";
  puts "";
  puts "  ant: 1a";
  puts "    Date:     Tue Aug 16 15:45:42 -0700 2016";
  puts "    Elev X:   5126821.0, 86717144.0, [97390880.0], 95370064.0, 9606030.0";
  puts "    Elev Y:   4150576.0, 96228960.0, [102588768.0], 98082336.0, 9055430.0";
  puts "    Az X:     3930998.0, 95498616.0, [97228808.0], 92609200.0, 8361026.0";
  puts "    Az Y:     3974478.0, 101007344.0, [102617344.0], 100567680.0, 5203159.0";
  puts "    Sat:      GPS-BIIR-9---PRN-21-";
  puts "      Az/El:    276.678 49.088";
  puts "    atasetpmoffsets --absolute 1a 290.7950 77.7110";
  puts "    XY New:   290.787825779867 77.6869849299829";
  puts "    XY Diff:  0.00717422013337909 0.0240150700170858";
  puts "    Cmd:      atasetpmoffsets --absolute 1a 290.787825779867 77.6869849299829";
  puts "    X New:    290.78161426603 77.6688532577884";
  puts "    X Diff:   0.0133857339696419 0.042146742211628";
  puts "    Cmd:      atasetpmoffsets --absolute 1a 290.78161426603 77.6688532577884";
  puts "    Y New:    290.793138884239 77.7026651372184";
  puts "    Y Diff:   0.00186111576118719 0.00833486278162354";
  puts "    Cmd:      atasetpmoffsets --absolute 1a 290.793138884239 77.7026651372184";
  puts "";
  puts "Elev X contains the 5 power mensurements for the X pol along the elevation direction.";
  puts "Elev Y contains the 5 power mensurements for the Y pol along the elevation direction.";
  puts "Az X contains the 5 power mensurements for the X pol along the azimuth direction.";
  puts "Az Y contains the 5 power mensurements for the Y pol along the azimuth direction.";
  puts "Az/El is the azimuth and elevation of the antenna after the last power measurement.";
  puts "The first atasetpmoffsets is the original pm offsets of this dish.";
  puts " First set of offsets are calculated averaging the X and Y pol values. ";
  puts "   XY New: the new pointing model offsets calulated suing the X/Y averages.";
  puts "   XY Diff: the difference of this calculated pm offsets from the original.";
  puts "   Cmd:      atasetpmoffsets --absolute ... is the command to apply this calculated offset.";
  puts " Second set of offsets are calculated just using the X pol power values. ";
  puts "   X New: the new pointing model offsets calulated suing the X pol power values.";
  puts "   X Diff: the difference of this calculated pm offsets from the original.";
  puts "   Cmd:      atasetpmoffsets --absolute ... is the command to apply this calculated offset.";
  puts " Third set of offsets are calculated just using the Y pol power values. ";
  puts "   X New: the new pointing model offsets calulated suing the Y pol power values.";
  puts "   X Diff: the difference of this calculated pm offsets from the original.";
  puts "   Cmd:      atasetpmoffsets --absolute ... is the command to apply this calculated offset.";
  puts "";
  puts "";
  puts "NOTES:";
  puts "   1: Karto suggests it is best to use the best pol for the pointing model corrections.";
  puts "   2: You may notice some squint, a few are quite bad. Use the pol without the squint.";
  puts "   3: The satellite selection only uses satellites above #{$elevLimit.to_s} degrees";
  puts "        and rising, less than #{($elevLimit + 20.0).to_s} degrees. Occasionally you ";
  puts "        may have to wait till a satellite meets this condition.";
  puts "";
  exit(1);

end

if(ARGV.length < 1) then printHelp(); end;

$ant = ARGV[0];

# Print the data/time for the log
time1 = Time.new.localtime
puts "Current Time : " + time1.to_s

# Get the ibob hookups
$hookups = IBOBRACK.new();

doCmd("/home/obs/ruby/bin/fxconf.rb sagive none fxa #{$ant}");
ants = Ants.new("fxa");

$satName = getSatBestRising();
if($satName.length < 2)
  puts "No rising GPS satellites with elevation between 40 and 55 degrees.";
  puts "Wait a bit and try again...";
  exit(1);
else
  puts "Best rising GPS Satellite = " + $satName;
end

ants = Ants.new("fxa");
ants.initAnts($satName, $freq);
ants.performMeasurements();
ants.moveAnts($antGroup, "none");

