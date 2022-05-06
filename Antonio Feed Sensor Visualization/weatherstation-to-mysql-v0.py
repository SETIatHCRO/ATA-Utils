# Program to collect the weatherstation data
# And send it to the mysql database on data.hcro.org


import telnetlib
import re
import mysql.connector
import logging



def conn_telnet_str(host):
        # telnet of secondary weatherstation
        HOST = host
        tn = telnetlib.Telnet(HOST,"4001",timeout= 2)

        # telnet output of the weatherstation in between two Id datasets (one complete Dataset)
        tn.read_until(b"Id=", timeout = None) 
        OUTPUT = tn.read_until(b"Id=",timeout = None)
        txt = str(OUTPUT) 
        tn.close()
        return txt



def main():
    # for errorlogging uncomment next two lines
    ## loggingpath = "weathererror.log"
    ## logging.basicConfig(filename=loggingpath,format='%(asctime)s %(message)s', filemode='w')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    try:          
        txt = conn_telnet_str("weatherport-secondary.hcro.org")
        conn_telnet2 = True
    except:
        logger.error("telnet connection for secondary weatherstation could not be established, default values will be send")
        conn_telnet2 = False
    
    try: 
        txt1 = conn_telnet_str("weatherport-primary.hcro.org") 
        conn_telnet1 = True
    except:
        logger.error("telnet connection for primary weatherstation could not be established, default values will be send")
        conn_telnet1 = False

    # default values for all measurements so in case anything fails still data gets send

    taflt = -99
    uaflt = -99
    paflt = -99
    riflt = -99
    dmflt = -99
    snflt = -99
    smflt = -99
    sxflt = -99
    rcflt = -99
    rdflt = -99
    hcflt = -99
    hdflt = -99
    hiflt = -99
    dnflt = -99
    dxflt = -99
    thflt = -99
    vhflt = -99
    vsflt = -99
    vrflt = -99
    taflt1 = -99
    uaflt1 = -99
    paflt1 = -99
    riflt1 = -99
    dmflt1 = -99
    snflt1 = -99
    smflt1 = -99
    sxflt1 = -99
    rcflt1 = -99
    rdflt1 = -99
    hcflt1 = -99
    hdflt1 = -99
    hiflt1 = -99
    dnflt1 = -99
    dxflt1 = -99
    thflt1 = -99
    vhflt1 = -99
    vsflt1 = -99
    vrflt1 = -99

    # secondary weatherstation
    if conn_telnet2:
        flg = False
        # Get Ta (outside_temp_c)
        try:
            pattern = "Ta=(.*?)C"
            tastr = re.search(pattern, txt).group(1)
            taflt = float(tastr)
        except:
            logger.warning("secondary outside_temp_c was unsuccessful")
            flg = True

        # Get Ua (outside_humidity_pct)
        try:
            pattern = "Ua=(.*?)P"
            uastr = re.search(pattern, txt).group(1)
            uaflt = float(uastr)
        except:
            logger.warning("secondary outside_humidity_pct was unsuccessful")
            flg = True

        # Get Pa (pressure_mb)
        try:
            pattern = "Pa=(.*?)H"
            pastr = re.search(pattern, txt).group(1)
            paflt = float(pastr)
        except:
            logger.warning("secondary pressure_mb was unsuccessful")
            flg = True

        # Get Ri (rain_rate_mm_hr)
        try:
            pattern = "Ri=(.*?)M"
            ristr = re.search(pattern, txt).group(1)
            riflt = float(ristr)
        except:
            logger.warning("secondary rain_rate_mm_hr was unsuccessful")
            flg = True

        # Get Dm (windspeed_dir_avg_deg)
        try:
            pattern = "Dm=(.*?)D"
            dmstr = re.search(pattern, txt).group(1)
            dmflt = float(dmstr)
        except:
            logger.warning("secondary windspeed_dir_avg_deg was unsuccessful")
            flg = True

        # Get Sn (windspeed_min_mph)
        try:
            pattern = "Sn=(.*?)S"
            snstr = re.search(pattern, txt).group(1)
            snflt = float(snstr)
        except:
            logger.warning("secondary windspeed_min_mph was unsuccessful")
            flg = True

        # Get Sm (windspeed_avg_mph)
        try:
            pattern = "Sm=(.*?)S"
            smstr = re.search(pattern, txt).group(1)
            smflt = float(smstr)
        except:
            logger.warning("secondary windspeed_avg_mph was unsuccessful")
            flg = True

        # Get Sx (windspeed_max_mph)
        try:
            pattern = "Sx=(.*?)S"
            sxstr = re.search(pattern, txt).group(1)
            sxflt = float(sxstr)
        except:
            logger.warning("secondary windspeed_max_mph was unsuccessful")
            flg = True

        # Get Rc (rain_accumulation_mm)
        try:
            pattern = "Rc=(.*?)M"
            rcstr = re.search(pattern,txt).group(1)
            rcflt = float(rcstr)
        except:
            logger.warning("secondary rain_accumulation was unsuccessful")
            flg = True

        # Get Rd (rain_duration_sec)
        try:
            pattern = "Rd=(.*?)s"
            rdstr = re.search(pattern,txt).group(1)
            rdflt = float(rdstr)
        except:
            logger.warning("secondary rain_duration was unsuccessful")
            flg = True

        # Get Hc (hail_accumulation_hts_cm)
        try:
            pattern = "Hc=(.*?)M"
            hcstr = re.search(pattern,txt).group(1)
            hcflt = float(hcstr)
        except:
            logger.warning("secondary hail_accumulation_hts_cm was unsuccessful")
            flg = True

        # Get Hd (hail_duration_sec)
        try:
            pattern = "Hd=(.*?)s"
            hdstr = re.search(pattern,txt).group(1)
            hdflt = float(hdstr)
        except:
            logger.warning("secondary hail_duration_sec was unsuccessful")
            flg = True

        # Get Hi (hail_intensity_hts_cmh)
        try:
            pattern = "Hi=(.*?)M"
            histr = re.search(pattern,txt).group(1)
            hiflt = float(histr)
        except:
            logger.warning("secondary hail_intensity_hts_cmh was unsuccessful")
            flg = True

        # Get Dn (wind_speed_dir_min_deg)
        try:
            pattern = "Dn=(.*?)D"
            dnstr = re.search(pattern,txt).group(1)
            dnflt = float(dnstr)
        except:
            logger.warning("secondary wind_speed_dir_min_deg was unsuccessful")
            flg = True

        # Get Dx (wind_speed_dir_max_deg)
        try:
            pattern = "Dx=(.*?)D"
            dxstr = re.search(pattern,txt).group(1)
            dxflt = float(dxstr)
        except:
            logger.warning("secondary wind_speed_dir_max_deg was unsuccessful")
            flg = True

        # Get Th (heating_temp_c)
        try:
            pattern = "Th=(.*?)C"
            thstr = re.search(pattern,txt).group(1)
            thflt = float(thstr)
        except:
            logger.warning("secondary heating_temp_c was unsuccessful")
            flg = True

        # Get Vh (heating_vltg) sometimes heating_voltage doesn't get transmitted as Vh=##V but as Vh=##N don't know why yet
        try:
            try:
                pattern = "Vh=(.*?)V"
                vhstr = re.search(pattern,txt).group(1)
                vhflt = float(vhstr)
            except:
                pattern = "Vh=(.*?)N"
                vhstr = re.search(pattern,txt).group(1)
                vhflt = float(vhstr)
        except:
            logger.warning("secondary heating_vltg was unsuccessful")
            flg = True

        # Get Vs (supply_vltg)
        try:
            pattern = "Vs=(.*?)V"
            vsstr = re.search(pattern,txt).group(1)
            vsflt = float(vsstr)
        except:
            logger.warning("secondary supply_vltg was unsuccesful")
            flg = True

        # Get Vr (ref_vltg)
        try:
            pattern = "Vr=(.*?)V"
            vrstr = re.search(pattern,txt).group(1)
            vrflt = float(vrstr)
        except:
            logger.warning("secondary ref_vltg was unsuccesful")
            flg = True

        if flg:
            print(txt)    
    
    # primary weatherstation
    if conn_telnet1:
        
        flg1 = False
        # Get Ta (outside_temp_c)
        try:
            pattern1 = "Ta=(.*?)C"
            tastr1 = re.search(pattern1, txt1).group(1)
            taflt1 = float(tastr1)
        except:
            logger.warning("primary outside_temp_c was unsuccessful")
            flg1 = True

        # Get Ua (outside_humidity_pct)
        try:
            pattern1 = "Ua=(.*?)P"
            uastr1 = re.search(pattern1, txt1).group(1)
            uaflt1 = float(uastr1)
        except:
            logger.warning("primary outside_humidity_pct was unsuccessful")
            flg1 = True

        # Get Pa (pressure_mb)
        try:
            pattern1 = "Pa=(.*?)H"
            pastr1 = re.search(pattern1, txt1).group(1)
            paflt1 = float(pastr1)
        except:
            logger.warning("primary pressure_mb was unsuccessful")
            flg1 = True

        # Get Ri (rain_rate_mm_hr)
        try:
            pattern1 = "Ri=(.*?)M"
            ristr1 = re.search(pattern1, txt1).group(1)
            riflt1 = float(ristr1)
        except:
            logger.warning("primary rain_rate_mm_hr was unsuccessful")
            flg1 = True

        # Get Dm (windspeed_dir_avg_deg)
        try:
            pattern1 = "Dm=(.*?)D"
            dmstr1 = re.search(pattern1, txt1).group(1)
            dmflt1 = float(dmstr1)
        except:
            logger.warning("primary windspeed_dir_avg_deg was unsuccessful")
            flg1 = True

        # Get Sn (windspeed_min_mph)
        try:
            pattern1 = "Sn=(.*?)S"
            snstr1 = re.search(pattern1, txt1).group(1)
            snflt1 = float(snstr1)
        except:
            logger.warning("primary windspeed_min_mph was unsuccessful")
            flg1 = True

        # Get Sm (windspeed_avg_mph)
        try:
            pattern1 = "Sm=(.*?)S"
            smstr1 = re.search(pattern1, txt1).group(1)
            smflt1 = float(smstr1)
        except:
            logger.warning("primary windspeed_avg_mph was unsuccessful")
            flg1 = True

        # Get Sx (windspeed_max_mph)
        try:
            pattern1 = "Sx=(.*?)S"
            sxstr1 = re.search(pattern1, txt1).group(1)
            sxflt1 = float(sxstr1)
        except:
            logger.warning("primary windspeed_max_mph was unsuccessful")
            flg1 = True

        # Get Rc (rain_accumulation_mm)
        try:
            pattern1 = "Rc=(.*?)M"
            rcstr1 = re.search(pattern1,txt1).group(1)
            rcflt1 = float(rcstr1)
        except:
            logger.warning("primary rain_accumulation_mm was unsuccessful")
            flg1 = True

        # Get Rd (rain_duration_sec)
        try:
            pattern1 = "Rd=(.*?)s"
            rdstr1 = re.search(pattern1,txt1).group(1)
            rdflt1 = float(rdstr1)
        except:
            logger.warning("primary rain_duration_sec was unsuccessful")
            flg1 = True

        # Get Hc (hail_accumulation_hts_cm)
        try:
            pattern1 = "Hc=(.*?)M"
            hcstr1 = re.search(pattern1,txt1).group(1)
            hcflt1 = float(hcstr1)
        except:
            logger.warning("primary_hail_accumulation_hts_cm was unsuccessful")
            flg1 = True

        # Get Hd (hail_duration_sec)
        try:
            pattern1 = "Hd=(.*?)s"
            hdstr1 = re.search(pattern1,txt1).group(1)
            hdflt1 = float(hdstr1)
        except:
            logger.warning("primary hail_duration_sec was unsuccessful")
            flg1 = True

        # Get Hi (hail_intensity_hts_cmh)
        try:
            pattern1 = "Hi=(.*?)M"
            histr1 = re.search(pattern1,txt1).group(1)
            hiflt1 = float(histr1)
        except:
            logger.warning("primary hail_intensity_hts_cmh was unsuccessful")
            flg1 = True

        # Get Dn (wind_speed_dir_min_deg)
        try:
            pattern1 = "Dn=(.*?)D"
            dnstr1 = re.search(pattern1,txt1).group(1)
            dnflt1 = float(dnstr1)
        except:
            logger.warning("primary wind_speed_dir_min_deg was unsuccessful")
            flg1 = True

        # Get Dx (wind_speed_dir_max_deg)
        try:
            pattern1 = "Dx=(.*?)D"
            dxstr1 = re.search(pattern1,txt1).group(1)
            dxflt1 = float(dxstr1)
        except:
            logger.warning("primary wind_speed_dir_max_deg was unsuccessful")
            flg1 = True

        # Get Th (heating_temp_c)
        try:
            pattern1 = "Th=(.*?)C"
            thstr1 = re.search(pattern1,txt1).group(1)
            thflt1 = float(thstr1)
        except:
            logger.warning("primary heating_temp_c was unsuccessful")
            flg1 = True

        # Get Vh (heating_vltg) sometimes heating_voltage doesn't get transmitted as Vh=##V but as Vh=##N don't know why yet
        try:
            try:
                pattern1 = "Vh=(.*?)V"
                vhstr1 = re.search(pattern1,txt1).group(1)
                vhflt1 = float(vhstr1)
            except:  
                pattern1 = "Vh=(.*?)N"
                vhstr1 = re.search(pattern1,txt1).group(1)
                vhflt1 = float(vhstr1)
        except:
            logger.warning("primary_heating_vltg was unsuccessful")
            flg1 = True

        # Get Vs (supply_vltg)
        try:
            pattern1 = "Vs=(.*?)V"
            vsstr1 = re.search(pattern1,txt1).group(1)
            vsflt1 = float(vsstr1)
        except:
            logger.warning("primary supply_vltg was unsuccessful")
            flg1 = True

        # Get Vr (ref_vltg)
        try:
            pattern1 = "Vr=(.*?)V"
            vrstr1 = re.search(pattern1,txt1).group(1)
            vrflt1 = float(vrstr1)
        except:
            logger.warning("primary ref_vltg was unsuccessful")
            flg1 = True
  
        if flg1:
            print(txt1)

    #establishing the connection
    try:
        conn = mysql.connector.connect(user='grafanauser', password='Mars2020', host='data.hcro.org', database='grafanadata', auth_plugin='mysql_native_password')
    except:
        logger.error("Connection to database failed")
    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    # Preparing SQL query to INSERT a record into the database.
    sql = f"""INSERT INTO weather\
        (secondary_outside_temp_c,\
        secondary_outside_humidity_pct,\
        secondary_pressure_mb,\
        secondary_rain_rate_mm_hr,\
        secondary_windspeed_dir_avg_deg,\
        secondary_windspeed_min_mph,\
        secondary_windspeed_avg_mph,\
        secondary_windspeed_max_mph,\
        secondary_rain_accumulation_mm,\
        secondary_rain_duration_sec,\
        secondary_hail_accumulation_hts_cm,\
        secondary_hail_duration_sec,\
        secondary_hail_intensity_hts_cmh,\
        secondary_windspeed_dir_min_deg,\
        secondary_windspeed_dir_max_deg,\
        secondary_heating_temp_c,\
        secondary_heating_vltg,\
        secondary_supply_vltg,\
        secondary_ref_vltg,\
        primary_outside_temp_c,\
        primary_outside_humidity_pct,\
        primary_pressure_mb,\
        primary_rain_rate_mm_hr,\
        primary_windspeed_dir_avg_deg,\
        primary_windspeed_min_mph,\
        primary_windspeed_avg_mph,\
        primary_windspeed_max_mph,\
        primary_rain_accumulation_mm,\
        primary_rain_duration_sec,\
        primary_hail_accumulation_hts_cm,\
        primary_hail_duration_sec,\
        primary_hail_intensity_hts_cmh,\
        primary_windspeed_dir_min_deg,\
        primary_windspeed_dir_max_deg,\
        primary_heating_temp_c,\
        primary_heating_vltg,\
        primary_supply_vltg,\
        primary_ref_vltg\
        )\
        VALUES ({taflt},{uaflt},{paflt},{riflt},{dmflt},{snflt},{smflt},{sxflt},{rcflt},{rdflt},{hcflt},{hdflt},{hiflt},{dnflt},{dxflt},{thflt},{vhflt},{vsflt},{vrflt},\
        {taflt1},{uaflt1},{paflt1},{riflt1},{dmflt1},{snflt1},{smflt1},{sxflt1},{rcflt1},{rdflt1},{hcflt1},{hdflt1},{hiflt1},{dnflt1},{dxflt1},{thflt1},{vhflt1},{vsflt1},{vrflt1})"""


    try:
        # Executing the SQL command
        cursor.execute(sql)
        print("cursor execute worked")
        # Commit your changes in the database
        conn.commit()
        print("successfully send data to database")
    except:
        # Rolling back in case of error
        conn.rollback()
        logger.error("failed to send data to database")

    # Closing the connection
    conn.close()

    # print(taflt)

if __name__ == "__main__":
    main()

