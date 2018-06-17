
class Address 

  attr_accessor :bfnum, :pol, :ipaddress, :port;

  def initialize(bfnum, pol, ipaddress, port)
    @bfnum = bfnum.to_s;
    @pol = pol.to_s;
    @ipaddress = ipaddress.to_s;
    @port = port.to_s;
  end

  def self.get(addressArray, bfnum, pol)
    addressArray.each do |a|
      if(a.to_i == a.bfnum.to_i && a.pol.eql?(pol)) then return a; end
    end
    return nil;
  end 

  def self.getDesc(addressArray)
    s = ""
    addressArray.each do |a|
      s += "\t\t BF" + a.bfnum + "." + a.pol + " " + a.ipaddress + ":" + a.port + "\n";
    end
    return s.chomp;
  end

end
