#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'time'
require 'fileutils'

$logfileName = nil;
REPORT_TYPE_ANTS=1
REPORT_TYPE_ATTN=2
REPORT_TYPE_DELAYCAL=3
REPORT_TYPE_PHASECAL=4
REPORT_TYPE_DATETIME=5


def makeAntReport()
	polListsx = Array.new($antPolList.length);
	polListsy = Array.new($antPolList.length);

	polListxIndex = 0;
	polListyIndex = 0;
	index = 0;
	polLists = [];


	$antPolList.each do |bfAnts|
		"xy".each_byte do |pol|

			pol = pol.chr;
			if(pol.eql?("x")) then index = polListxIndex; end
			if(pol.eql?("y")) then index = polListyIndex; end

			parts = bfAnts.split(",");
			parts.each do |antpol|
				if(antpol.include?(pol))
					if(pol.eql?("x")) 
						if(polListsx[index] == nil) then polListsx[index] = []; end
						polListsx[index] << antpol[0..-3];
					end
					if(pol.eql?("y")) 
						if(polListsy[index] == nil) then polListsy[index] = []; end
						polListsy[index] << antpol[0..-3];
					end
					#polLists[index] << antpol[0..-3];
					#puts polLists[index].to_s	
					#puts antpol[0..-3];
				end
			end
			if(pol.eql?("x")) then polListxIndex += 1; end
			if(pol.eql?("y")) then polListyIndex += 1; end
		end
	end

	result = "";
	index = 0;
	polListsx.each do |list|
		result += "BF" + (index + 1).to_s + " x: ";
		list.each do |ant|
			result += ant + ",";
		end
		result = result.chop + "\n";
		index += 1;
	end
	index = 0;
	polListsy.each do |list|
		result += "BF" + (index + 1).to_s + " y: ";
		list.each do |ant|
			result += ant + ",";
		end
		result = result.chop + "\n";
		index += 1;
	end
#	puts result;
	return result;
end


def getHookup(aorb, pol)
#  > hookups bfa -a 1a
#1ax	-	in0.i01.bfa	x0.f1.b01	x0.f3.b01	x0.f3.b05	
#1ay	-	in0.i13.bfa	x0.f1.b03	x0.f3.b03	x0.f2.b05
	cmd = "hookups bf" + aorb + " -a " + pol;
	result = `#{cmd}`;
        # puts cmd;
        # puts result;
	if(result != nil && result.length > 10)
		result.each_line do |line|
			if(!line.include?(pol)) then next; end
			parts = line.split(/\s+/);
			parts2 = parts[2].split(".");	
			# "in0.i01.bfa" to "i1.bfa in0"
			return (parts2[1] + "." + parts2[2] + " " + parts2[0]).gsub("i0", "i");
		end
	end
	return nil;
end

def makeAttnReport(attnResult)

puts "ATTN REPRT=";
puts attnResult;

	index = 0;
	result = "";
	$antPolList.each do |bfPolList|
		bf = "b";
		if(index == 0)
			bf = "a";
		end
		if(index == 0)
			result += "\nBFA: \n";
		else 
			result += "\nBFB: \n";
		end

		pols = bfPolList.split(",");
		pols.each do |pol|
		 	hookup = getHookup(bf, pol[0..-2]);
			#puts hookup;
			attnResult.each_line do |line|
				#setatten.rb i5.bfb in1 20.0 0 ;: Got 10.5 RMS, wanted 11.0 +/- 0.5 ;
				#setatten.rb i6.bfb in1 31.5 0 ;: Input level too low.  Min atten got 2.5 RMS, wanted 11.0 +/- 0.5 ;
				if(!line.include?(hookup)) then next; end
				parts = line.chop.split(":");
				parts2 = line.split(/\s+/);
				result += "\t" + pol[0..-2] + ": " + parts2[3] + "dB " + parts[1] + " (" + parts2[2] + "." + parts2[1] + "a)\n";
			end
		end
		index += 1;
	end

	return result;
	
end

def createReport(reportText, reportType)

#return "XX";

	if(reportType == REPORT_TYPE_ANTS)

		result = makeAntReport();
		if($logfileName == nil) then puts result; return; end
		open($logfileName, 'a') { |f|
			f.puts "Antennas:\n";
			f.puts result + "\n";
		}
	elsif(reportType == REPORT_TYPE_ATTN)
		result = makeAttnReport(reportText);
		if($logfileName == nil) then puts result; return; end
		open($logfileName, 'a') { |f|
			f.puts "ATTENUATION:\n";
			f.puts "#{result}\n";
		}
	elsif(reportType == REPORT_TYPE_DELAYCAL)
		result = makeCalReport(reportText);
		if($logfileName == nil) then puts result; return; end
		open($logfileName, 'a') { |f|
			f.puts "DELAY CAL:\n";
			f.puts "#{result}\n";
		}
	elsif(reportType == REPORT_TYPE_PHASECAL)
		result = makeCalReport(reportText);
		if($logfileName == nil) then puts result; return; end
		open($logfileName, 'a') { |f|
			f.puts "PHASE CAL:\n";
			f.puts "#{result}\n";
		}
	elsif(reportType == REPORT_TYPE_DATETIME)
		result = Time.now.utc.strftime("%b %d, %Y %H:%M");
		if($logfileName == nil) then puts result; return; end
		open($logfileName, 'a') { |f|
			f.puts "DATETIME: #{result} UTC\n\n";
		}
	end
end

def setLogfileName(filename)
	$logfileName = filename;
	if(File.exist?(filename)) then return true; end
	return false;
end

def makeCalReport(delayCal)
	#| Beam Former: 1 (1-3)
	bfStats = nil;
	result = "";
	delayCal.each_line do |line|
		if(line.include?("Beam Former:"))
			parts = line.split(/\s+/);
			bfNum = parts[3];
			result += "\nBF " + bfNum + "\n";
		end
		#/----------------Statistics---------------(Mode 1)------------------
		#\----------------End Statistics------------------------------------------
		if(line.include?("--Statistics---"))
			 bfStats = "\n\n";
		elsif(bfStats != nil)
			if(line.include?("--End Statistics---"))
				result += bfStats;
				bfStats = nil;
			else
				bfStats += line;
			end
		end
	end

	return result;
end

if __FILE__==$0
	puts makeAntReport();
	puts makeAttnReport(IO.read(ARGV[0]));
	puts "\n***\nDELAY CALIBRATION:\n\n";
	puts makeCalReport(IO.read(ARGV[1]));
	puts "\n***\nPHASE CALIBRATION:\n\n";
	puts makeCalReport(IO.read(ARGV[2]));
end
