from SNAPobs import snap_if

ant_list = ["1c", "1e", "1g", "1h", "1k", "2a", "2b", "2c",
            "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
            "4j", "5b", "4g"]

lo = "B"
antlo_list = [ant+lo for ant in ant_list]

ifs  = {antlo+pol:20 for antlo in antlo_list for pol in ["x","y"]}

snap_if.setatten(ifs)
