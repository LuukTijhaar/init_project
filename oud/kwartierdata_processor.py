import streamlit as st
import pandas as pd
import numpy as np
import matplotlib 
matplotlib.use('TkAgg')  # Use a non-interactive backend for matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from typing import Literal, TypedDict 
import seaborn as sns

correctiewaarden = {
    "oost": {
        0:  {"factor": 0.8,  "tijd": -0.0},   # 30 minuten eerder
        15: {"factor": 0.79, "tijd": -0.30},
        45: {"factor": 0.72, "tijd": -0.45},
        90: {"factor": 0.46, "tijd": -0.60},
        "default": {"factor": 0.46, "tijd": -0.35}
    },
    "west": {
        0:  {"factor": 0.8,  "tijd": 0.0},    # 30 minuten later
        15: {"factor": 0.79, "tijd": 0.30},
        45: {"factor": 0.71, "tijd": 0.45},
        90: {"factor": 0.45, "tijd": 0.60},
        "default": {"factor": 0.45, "tijd": 0.35}
    },
    "zuid": {
        0:  {"factor": 0.8,  "tijd": 0},
        15: {"factor": 0.88, "tijd": 0},
        45: {"factor": 0.91, "tijd": 0},
        90: {"factor": 0.64, "tijd": 0},
        "default": {"factor": 0.64, "tijd": 0}
    },
    "noord": {
        0:  {"factor": 0.8,  "tijd": 0},   # nauwelijks zon: tijd niet zinvol
        15: {"factor": 0.69, "tijd": 0},
        45: {"factor": 0.44, "tijd": 0},
        90: {"factor": 0.18, "tijd": 0},
        "default": {"factor": 0.18, "tijd": 0}
    },
    "zuidoost": {
        0:  {"factor": 0.8,  "tijd": -0},
        15: {"factor": 0.86, "tijd": -0.15},
        45: {"factor": 0.86, "tijd": -0.25},
        90: {"factor": 0.6, "tijd": -0.35},
        "default": {"factor": 0.6, "tijd": -25}
    },
    "zuidwest": {
        0:  {"factor": 0.8,  "tijd": 0},
        15: {"factor": 0.86, "tijd": 0.15},
        45: {"factor": 0.86, "tijd": 0.25},
        90: {"factor": 0.59, "tijd": 0.35},
        "default": {"factor": 0.59, "tijd": 25}
    },
    "noordoost": {
        0:  {"factor": 0.8,  "tijd": -0},
        15: {"factor": 0.72, "tijd": -0.15},
        45: {"factor": 0.54, "tijd": -0.25},
        90: {"factor": 0.28, "tijd": -0.35},
        "default": {"factor": 0.28, "tijd": -70}
    },
    "noordwest": {
        0:  {"factor": 0.8,  "tijd": 0},
        15: {"factor": 0.72, "tijd": 0.15},
        45: {"factor": 0.54, "tijd": 0.25},
        90: {"factor": 0.27, "tijd": 0.35},
        "default": {"factor": 0.27, "tijd": 70}
    }
}

def get_orientatie_data(orientatie, helling):
    if helling == 0:
        return 0.8, 0  # overal gelijk bij 0°
    orientatie = orientatie.lower()
    waarden = correctiewaarden.get(orientatie, {})
    data = waarden.get(helling, waarden.get("default", {"factor": 0.5, "tijd": 0}))
    return data["factor"], data["tijd"]

class KwartierdataProcessor:
    def __init__(self, aantal_jaren:Literal[1,2], breedtegraad:float, lengtegraad:float, hellingshoek1:Literal[0,15,45,90], hellingshoek2:Literal[0,15,45,90], 
                 orientatie1:Literal["oost","west","zuid","noord","zuidoost","zuidwest","noordoost","noordwest"], orientatie2:Literal["oost","west","zuid","noord","zuidoost","zuidwest","noordoost","noordwest"], 
                 wp1:float, wp2:float, begin_dag:str, zonnedata_pos:bool, rendement:float, omvormer:float=100000000, data=None):
        self.aantal_jaren = aantal_jaren
        self.breedtegraad = breedtegraad
        self.lengtegraad = lengtegraad
        self.omvormer = omvormer
        self.hellingshoek1 = hellingshoek1
        self.hellingshoek2 = hellingshoek2
        self.orientatie1 = orientatie1
        self.orientatie2 = orientatie2
        self.wp1 = wp1
        self.wp2 = wp2
        self.begin_dag = pd.to_datetime(begin_dag)
        self.zonnedata_pos = zonnedata_pos
        if self.zonnedata_pos:
            self.zonnedata_pos = 1
        else: 
            self.zonnedata_pos = -1
        self.rendement = rendement
        self.data = data
        
        self.orientatiefactor1, self.tijdcorrectie1 = get_orientatie_data(self.orientatie1, self.hellingshoek1)
        self.orientatiefactor2, self.tijdcorrectie2 = get_orientatie_data(self.orientatie2, self.hellingshoek2)
        """self.tijdscorrectie1 = pd.Timedelta(minutes=self.tijdcorrectie1)
        self.tijdscorrectie2 = pd.Timedelta(minutes=self.tijdcorrectie2)"""
        self.dagen = pd.date_range(start='2023-01-01', periods=365 * aantal_jaren, freq='D')
        

        self.declinatie_vd_zon = [
            -9.821256059,-9.7874008,-9.750645323,-9.711000519,-9.668478136,-9.623090775,-9.574851884,-9.523775757,-9.469877531,-9.413173175,-9.353679493,-9.291414114,-9.226395488,-9.158642883,-9.088176373,-9.015016841,-8.939185965,-8.860706215,-8.779600847,-8.695893893,-8.609610159,-8.520775211,-8.429415374,-8.335557718,-8.239230058,-8.140460935,-8.039279618,-7.93571609,-7.829801037,-7.721565845,-7.611042587,-7.498264012,-7.38326354,-7.266075248,-7.14673386,-7.025274742,-6.901733882,-6.77614789,-6.64855398,-6.518989959,-6.387494221,-6.25410573,-6.118864013,-5.981809144,-5.842981736,-5.702422927,-5.560174367,-5.416278207,-5.270777086,-5.123714121,-4.975132889,-4.825077418,-4.673592172,-4.520722039,-4.36651232,-4.211008708,-4.054257284,-3.896304495,-3.737197148,-3.576982388,-3.415707692,-3.253420847,-3.090169944,-2.926003356,-2.760969731,-2.595117971,-2.428497221,-2.261156855,-2.09314646,-1.92451582,-1.755314904,-1.585593851,-1.415402952,-1.244792639,-1.073813467,-0.9025161,-0.730951299,-0.559169901,-0.387222809,-0.215160974,-0.043035383,0.129102961,0.301203048,0.473213883,0.645084494,0.816763953,0.988201387,1.159345996,1.330147065,1.500553983,1.670516255,1.839983517,2.008905551,2.177232304,2.344913896,2.511900639,2.678143052,2.843591873,3.008198076,3.171912886,3.334687789,3.496474553,3.657225235,3.816892203,3.975428143,4.132786078,4.288919379,4.443781781,4.597327395,4.749510721,4.900286664,5.049610547,5.197438122,5.343725583,5.488429583,5.631507243,5.772916166,5.912614449,6.050560696,6.186714033,6.321034112,6.453481132,6.584015847,6.712599576,6.839194216,6.963762256,7.086266783,7.206671496,7.324940716,7.441039399,7.554933141,7.666588193,7.77597147,7.883050558,7.987793729,8.090169944,8.190148867,8.287700872,8.382797052,8.475409229,8.565509959,8.653072544,8.738071036,8.82048025,8.900275764,8.977433935,9.051931899,9.12374758,9.192859697,9.259247772,9.322892132,9.383773917,9.441875088,9.497178428,9.549667549,9.599326897,9.646141757,9.690098257,9.731183372,9.769384928,9.804691604,9.837092938,9.866579329,9.89314204,9.916773199,9.937465804,9.955213724,9.970011699,9.981855345,9.990741151,9.996666485,9.999629591,9.999629591,9.996666485,9.990741151,9.981855345,9.970011699,9.955213724,9.937465804,9.916773199,9.89314204,9.866579329,9.837092938,9.804691604,9.769384928,9.731183372,9.690098257,9.646141757,9.599326897,9.549667549,9.497178428,9.441875088,9.383773917,9.322892132,9.259247772,9.192859697,9.12374758,9.051931899,8.977433935,8.900275764,8.82048025,8.738071036,8.653072544,8.565509959,8.475409229,8.382797052,8.287700872,8.190148867,8.090169944,7.987793729,7.883050558,7.77597147,7.666588193,7.554933141,7.441039399,7.324940716,7.206671496,7.086266783,6.963762256,6.839194216,6.712599576,6.584015847,6.453481132,6.321034112,6.186714033,6.050560696,5.912614449,5.772916166,5.631507243,5.488429583,5.343725583,5.197438122,5.049610547,4.900286664,4.749510721,4.597327395,4.443781781,4.288919379,4.132786078,3.975428143,3.816892203,3.657225235,3.496474553,3.334687789,3.171912886,3.008198076,2.843591873,2.678143052,2.511900639,2.344913896,2.177232304,2.008905551,1.839983517,1.670516255,1.500553983,1.330147065,1.159345996,0.988201387,0.816763953,0.645084494,0.473213883,0.301203048,0.129102961,-0.043035383,-0.215160974,-0.387222809,-0.559169901,-0.730951299,-0.9025161,-1.073813467,-1.244792639,-1.415402952,-1.585593851,-1.755314904,-1.92451582,-2.09314646,-2.261156855,-2.428497221,-2.595117971,-2.760969731,-2.926003356,-3.090169944,-3.253420847,-3.415707692,-3.576982388,-3.737197148,-3.896304495,-4.054257284,-4.211008708,-4.36651232,-4.520722039,-4.673592172,-4.825077418,-4.975132889,-5.123714121,-5.270777086,-5.416278207,-5.560174367,-5.702422927,-5.842981736,-5.981809144,-6.118864013,-6.25410573,-6.387494221,-6.518989959,-6.64855398,-6.77614789,-6.901733882,-7.025274742,-7.14673386,-7.266075248,-7.38326354,-7.498264012,-7.611042587,-7.721565845,-7.829801037,-7.93571609,-8.039279618,-8.140460935,-8.239230058,-8.335557718,-8.429415374,-8.520775211,-8.609610159,-8.695893893,-8.779600847,-8.860706215,-8.939185965,-9.015016841,-9.088176373,-9.158642883,-9.226395488,-9.291414114,-9.353679493,-9.413173175,-9.469877531,-9.523775757,-9.574851884,-9.623090775,-9.668478136,-9.711000519,-9.750645323,-9.7874008,-9.821256059,-9.852201068,-9.880226657,-9.905324521,-9.927487225,-9.946708199,-9.962981749,-9.976303053,-9.986668163,-9.994074007,-9.998518392,-10,-9.998518392,-9.994074007,-9.986668163,-9.976303053,-9.962981749,-9.946708199,-9.927487225,-9.905324521,-9.880226657,-9.852201068] 
        self.equation_of_time = [
            3.705178323,4.149710085,4.589420831,5.023906865,5.452770624,5.875621107,6.292074307,6.701753633,7.104290318,7.499323825,7.886502235,8.265482636,8.635931491,8.997524999,9.349949446,9.692901542,10.02608875,10.34922958,10.66205393,10.96430334,11.25573125,11.53610331,11.80519758,12.06280479,12.30872852,12.54278545,12.76480551,12.97463203,13.17212197,13.35714598,13.52958854,13.68934812,13.83633719,13.97048235,14.09172437,14.20001822,14.29533312,14.37765251,14.44697408,14.50330972,14.54668549,14.57714155,14.59473209,14.59952526,14.59160302,14.57106105,14.5380086,14.49256835,14.43487621,14.36508116,14.28334504,14.18984234,14.08475995,13.96829696,13.84066434,13.70208473,13.55279212,13.39303156,13.22305883,13.04314016,12.85355186,12.65458,12.44652001,12.22967636,12.00436216,11.77089877,11.52961542,11.28084876,11.02494251,10.76224699,10.49311871,10.21791993,9.937018221,9.650786013,9.359600141,9.063841392,8.76389404,8.46014538,8.152985263,7.842805622,7.53,7.214963077,6.898090192,6.579776874,6.260418358,5.940409122,5.620142406,5.300009747,4.980400508,4.661701416,4.344296101,4.028564639,3.714883098,3.403623099,3.095151366,2.789829299,2.488012545,2.190050577,1.896286283,1.607055565,1.32268694,1.04350116,0.76981083,0.50192005,0.240124058,-0.015291117,-0.26404898,-0.505882896,-0.740536395,-0.967763466,-1.187328841,-1.399008264,-1.602588745,-1.797868799,-1.984658678,-2.162780581,-2.33206885,-2.492370155,-2.643543664,-2.785461189,-2.918007329,-3.041079587,-3.154588479,-3.258457618,-3.352623794,-3.437037027,-3.511660607,-3.576471122,-3.631458464,-3.676625824,-3.711989664,-3.73757968,-3.753438744,-3.759622832,-3.756200936,-3.743254959,-3.720879594,-3.68918219,-3.648282601,-3.598313016,-3.539417782,-3.471753206,-3.395487343,-3.310799771,-3.217881355,-3.116933989,-3.008170332,-2.89181353,-2.768096921,-2.637263732,-2.499566758,-2.355268041,-2.204638523,-2.047957698,-1.885513253,-1.717600692,-1.54452296,-1.366590051,-1.184118607,-0.997431517,-0.806857499,-0.612730678,-0.415390161,-0.215179599,-0.01244675,0.192456965,0.399176917,0.607355714,0.816633667,1.026649242,1.237039527,1.447440694,1.657488464,1.866818573,2.07506724,2.281871628,2.486870313,2.689703744,2.890014704,3.087448769,3.281654762,3.472285204,3.658996762,3.841450688,4.019313257,4.192256196,4.359957113,4.522099904,4.678375174,4.828480628,4.972121471,5.10901079,5.238869927,5.361428846,5.476426486,5.583611106,5.682740616,5.773582899,5.855916121,5.929529024,5.994221215,6.049803435,6.096097816,6.132938123,6.160169991,6.177651132,6.185251544,6.18285369,6.170352676,6.147656406,6.114685717,6.071374512,6.017669867,5.95353212,5.878934956,5.793865464,5.698324182,5.592325129,5.475895815,5.34907724,5.21192387,5.064503607,4.906897732,4.739200836,4.561520738,4.373978384,4.176707727,3.969855597,3.753581554,3.528057721,3.293468606,3.050010911,2.797893316,2.537336264,2.268571716,1.991842902,1.707404055,1.415520131,1.116466516,0.810528721,0.498002064,0.179191339,-0.145589523,-0.476017811,-0.811762395,-1.152484101,-1.497836097,-1.847464288,-2.201007715,-2.558098971,-2.91836462,-3.281425623,-3.646897778,-4.014392154,-4.383515548,-4.75387093,-5.125057907,-5.496673183,-5.868311031,-6.239563755,-6.610022174,-6.979276087,-7.346914762,-7.712527403,-8.075703639,-8.436034,-8.793110394,-9.146526588,-9.495878685,-9.840765595,-10.18078951,-10.51555636,-10.84467631,-11.16776419,-11.48443993,-11.79432908,-12.09706319,-12.39228026,-12.6796252,-12.95875021,-13.22931523,-13.49098832,-13.74344607,-13.986374,-14.21946689,-14.44242921,-14.65497542,-14.85683037,-15.04772957,-15.22741956,-15.3956582,-15.55221497,-15.69687124,-15.82942057,-15.94966891,-16.05743491,-16.15255008,-16.23485907,-16.30421979,-16.36050366,-16.40359574,-16.43339488,-16.44981387,-16.45277955,-16.44223292,-16.4181292,-16.38043796,-16.32914309,-16.2642429,-16.18575014,-16.09369195,-15.98810992,-15.86905999,-15.73661245,-15.59085188,-15.43187705,-15.25980081,-15.07475004,-14.87686544,-14.66630145,-14.44322608,-14.20782072,-13.96027993,-13.7008113,-13.42963515,-13.14698436,-12.85310408,-12.54825148,-12.23269548,-11.90671645,-11.57060589,-11.22466614,-10.86921005,-10.5045606,-10.1310506,-9.749022277,-9.358826931,-8.960824534,-8.55538334,-8.142879475,-7.723696523,-7.298225106,-6.866862448,-6.430011938,-5.988082685,-5.541489061,-5.090650249,-4.635989774,-4.177935034,-3.716916827,-3.253368877,-2.787727348,-2.320430364,-1.851917522,-1.382629407,-0.9130071,-0.443491692,0.025476204,0.493456942,0.96001233,1.424706115,1.887104464,2.346776445,2.8032945,3.256234924]
        self.T = [
            0.193819871,0.193889033,0.193963991,0.194044722,0.194131201,0.194223404,0.194321303,0.19442487,0.194534072,0.194648879,0.194769255,0.194895166,0.195026574,0.19516344,0.195305724,0.195453383,0.195606373,0.19576465,0.195928166,0.196096873,0.196270721,0.196449658,0.196633632,0.196822587,0.197016469,0.197215219,0.197418778,0.197627087,0.197840083,0.198057703,0.198279884,0.198506558,0.19873766,0.198973119,0.199212868,0.199456833,0.199704945,0.199957128,0.200213308,0.200473409,0.200737354,0.201005065,0.201276463,0.201551466,0.201829995,0.202111965,0.202397294,0.202685897,0.202977688,0.203272581,0.203570489,0.203871323,0.204174995,0.204481413,0.204790488,0.205102128,0.20541624,0.205732732,0.206051509,0.206372478,0.206695542,0.207020607,0.207347576,0.207676351,0.208006837,0.208338934,0.208672545,0.20900757,0.20934391,0.209681466,0.210020137,0.210359824,0.210700425,0.211041839,0.211383966,0.211726704,0.212069951,0.212413607,0.212757568,0.213101733,0.213446,0.213790267,0.214134432,0.214478393,0.214822049,0.215165296,0.215508034,0.215850161,0.216191575,0.216532176,0.216871863,0.217210534,0.21754809,0.21788443,0.218219455,0.218553066,0.218885163,0.219215649,0.219544424,0.219871393,0.220196458,0.220519522,0.220840491,0.221159268,0.22147576,0.221789872,0.222101512,0.222410587,0.222717005,0.223020677,0.223321511,0.223619419,0.223914312,0.224206103,0.224494706,0.224780035,0.225062005,0.225340534,0.225615537,0.225886935,0.226154646,0.226418591,0.226678692,0.226934872,0.227187055,0.227435167,0.227679132,0.227918881,0.22815434,0.228385442,0.228612116,0.228834297,0.229051917,0.229264913,0.229473222,0.229676781,0.229875531,0.230069413,0.230258368,0.230442342,0.230621279,0.230795127,0.230963834,0.23112735,0.231285627,0.231438617,0.231586276,0.23172856,0.231865426,0.231996834,0.232122745,0.232243121,0.232357928,0.23246713,0.232570697,0.232668596,0.232760799,0.232847278,0.232928009,0.233002967,0.233072129,0.233135476,0.233192989,0.23324465,0.233290444,0.233330358,0.23336438,0.233392499,0.233414708,0.233431,0.23344137,0.233445815,0.233444333,0.233436926,0.233423594,0.233404343,0.233379178,0.233348106,0.233311137,0.233268281,0.233219552,0.233164963,0.233104531,0.233038274,0.232966211,0.232888364,0.232804756,0.232715411,0.232620356,0.23251962,0.232413232,0.232301223,0.232183627,0.232060479,0.231931814,0.231797673,0.231658093,0.231513116,0.231362786,0.231207146,0.231046244,0.230880126,0.230708843,0.230532443,0.230350981,0.23016451,0.229973084,0.229776761,0.229575599,0.229369657,0.229158997,0.228943681,0.228723772,0.228499337,0.22827044,0.228037151,0.227799538,0.227557672,0.227311625,0.227061468,0.226807277,0.226549127,0.226287094,0.226021256,0.225751692,0.225478481,0.225201705,0.224921445,0.224637785,0.224350809,0.224060601,0.223767248,0.223470836,0.223171454,0.22286919,0.222564134,0.222256376,0.221946007,0.221633119,0.221317806,0.221000159,0.220680275,0.220358246,0.22003417,0.219708141,0.219380256,0.219050614,0.21871931,0.218386444,0.218052113,0.217716418,0.217379458,0.217041332,0.21670214,0.216361984,0.216020964,0.21567918,0.215336735,0.21499373,0.214650266,0.214306445,0.213962369,0.21361814,0.21327386,0.212929631,0.212585555,0.212241734,0.21189827,0.211555265,0.21121282,0.210871036,0.210530016,0.21018986,0.209850668,0.209512542,0.209175582,0.208839887,0.208505556,0.20817269,0.207841386,0.207511744,0.207183859,0.20685783,0.206533754,0.206211725,0.205891841,0.205574194,0.205258881,0.204945993,0.204635624,0.204327866,0.20402281,0.203720546,0.203421164,0.203124752,0.202831399,0.202541191,0.202254215,0.201970555,0.201690295,0.201413519,0.201140308,0.200870744,0.200604906,0.200342873,0.200084723,0.199830532,0.199580375,0.199334328,0.199092462,0.198854849,0.19862156,0.198392663,0.198168228,0.197948319,0.197733003,0.197522343,0.197316401,0.197115239,0.196918916,0.19672749,0.196541019,0.196359557,0.196183157,0.196011874,0.195845756,0.195684854,0.195529214,0.195378884,0.195233907,0.195094327,0.194960186,0.194831521,0.194708373,0.194590777,0.194478768,0.19437238,0.194271644,0.194176589,0.194087244,0.194003636,0.193925789,0.193853726,0.193787469,0.193727037,0.193672448,0.193623719,0.193580863,0.193543894,0.193512822,0.193487657,0.193468406,0.193455074,0.193447667,0.193446185,0.19345063,0.193461,0.193477292,0.193499501,0.19352762,0.193561642,0.193601556,0.19364735,0.193699011,0.193756524]

        self.Kwartieren = np.arange(0,24,0.25)
        self.df = pd.DataFrame(index=self.dagen, columns=self.Kwartieren)
        
    def bereken_kwartieropbrengst(_self):
        # Bereken de opbrengst per kwartier
        Opbrengsten1 = []
        Opbrengsten2 = []
        Opbrengst1_per_dag = []
        Opbrengst2_per_dag = []
        for dag in range(0, len(_self.dagen)):
            dag_opbrengst1 = 0
            dag_opbrengst2 = 0   
            for kwartier in _self.Kwartieren:
                # Hier komt de logica voor het berekenen van de opbrengst per kwartier
                h1 = 15*((kwartier-1+_self.tijdcorrectie1)+_self.lengtegraad/15+_self.equation_of_time[dag]/60-12)
                h2 = 15*((kwartier-1+_self.tijdcorrectie2)+_self.lengtegraad/15+_self.equation_of_time[dag]/60-12)  
                cos_Z1 = np.sin(np.radians(_self.breedtegraad)) * np.sin(np.radians(_self.declinatie_vd_zon[dag])) + np.cos(np.radians(_self.breedtegraad)) * np.cos(np.radians(_self.declinatie_vd_zon[dag])) * np.cos(np.radians(h1))
                cos_Z2 = np.sin(np.radians(_self.breedtegraad)) * np.sin(np.radians(_self.declinatie_vd_zon[dag])) + np.cos(np.radians(_self.breedtegraad)) * np.cos(np.radians(_self.declinatie_vd_zon[dag])) * np.cos(np.radians(h2))
                zonnezenithoek1 = np.degrees(np.arccos(cos_Z1))
                zonnezenithoek2 = np.degrees(np.arccos(cos_Z2))
                
                if zonnezenithoek1 < 90:
                    intensiteitsfactor1 = 1361 * np.cos(np.radians(zonnezenithoek1))*_self.T[dag] 
                    if intensiteitsfactor1 > 75:
                        Pos_intensiteit1 = intensiteitsfactor1 ** 1.8
                        factor1 = Pos_intensiteit1/1020/26*_self.orientatiefactor1*0.95
                        opbrengst1 = _self.wp1 * factor1 /4000
                        Opbrengsten1.append(float(opbrengst1))
                    else:
                        opbrengst1 = 0
                        Opbrengsten1.append(0)
                else:
                    opbrengst1 = 0
                    Opbrengsten1.append(0)


                if zonnezenithoek2 < 90:
                    intensiteitsfactor2 = 1361 * np.cos(np.radians(zonnezenithoek2))*_self.T[dag] 
                    if intensiteitsfactor2 > 75:
                        Pos_intensiteit2 = intensiteitsfactor2 ** 1.8
                        factor2 = Pos_intensiteit2/1020/26*_self.orientatiefactor2*0.95
                        opbrengst2 = _self.wp2 * factor2 / 4000
                        Opbrengsten2.append(float(opbrengst2))
                    else:
                        opbrengst2 = 0
                        Opbrengsten2.append(0)
                else:
                    opbrengst2 = 0  
                    Opbrengsten2.append(0)  
                

                dag_opbrengst1 = dag_opbrengst1+ opbrengst1
                dag_opbrengst2 = dag_opbrengst2+ opbrengst2
            Opbrengst1_per_dag.append(dag_opbrengst1)
            Opbrengst2_per_dag.append(dag_opbrengst2)   

                            
        # Genereer datetime index per 15 minuten in 2024 (voorbeeldjaar)
        timestamps = pd.date_range(start="2023-01-01 00:00", end="2023-12-31 23:45", freq="15min")
        # Controleer of de lengte van de opbrengsten overeenkomt met de timestamps

                    
        print(sum(Opbrengsten1), sum(Opbrengsten2))  # Totale opbrengst voor controle
        # Stop in DataFrame
        Opbrengsten1 = pd.Series(Opbrengsten1, index=timestamps)
        Opbrengsten2 = pd.Series(Opbrengsten2, index=timestamps)
        Opbrengsten1 = Opbrengsten1*_self.zonnedata_pos/1000
        Opbrengsten2 = Opbrengsten2*_self.zonnedata_pos/1000            
        Opbrengsten_samen = Opbrengsten1 + Opbrengsten2
        Opbrengsten_samen.name = "Opbrengst"
        Opbrengsten_samen.index = timestamps
        Opbrengsten_samen.index.name = "Tijdstip"
        for index in range(len(Opbrengsten_samen)): 
            Opbrengsten_samen[index] = min(Opbrengsten_samen[index], _self.omvormer)
        return Opbrengsten_samen   

def kwartierdata_naar_dagdata(df:pd.DataFrame, tijdstip_col=0, waarde_col=1):
    """
    Zet kwartierdata om naar dagdata door op te tellen per dag.
    
    Parameters:
    - df: pandas DataFrame met kolommen als nummers
    - tijdstip_col: kolomnummer van de tijdstippen (index)
    - waarde_col: kolomnummer van de waarden (verbruik/opwek)
    
    Returns:
    - Een DataFrame met dagtotalen
    """
    df = df.copy()
    
    #assert waarde_col < df.shape[1], "waarde_col is buiten kolomrange"
    
    # Resample op dagbasis en sommeer de waarden
    if len(df.columns) == 1:
        dagdata = df.iloc[:, [waarde_col-1]].resample('D').sum()
    else:
        dagdata = df.iloc[:, [waarde_col-1, waarde_col]].resample('D').sum()
    return dagdata
        
def read_data(file_path):
    df = pd.read_excel(file_path)
    #print(type(df))
    df_klein = df[["Tijdstip", "Verbruik"]].copy()
    df_klein['Tijdstip'] = pd.to_datetime(df_klein['Tijdstip'], format="%d-%m-%Y %H:%M")
    df_klein.set_index('Tijdstip', inplace=True)
    df_klein = df_klein.head(35040)
    return df_klein

def normaliseer_data(df, ref_data):
    Totaal_df = sum(df['opbrengst1_W']) + sum(df['opbrengst2_W'])
    Totaal_ref = ref_data["Verbruik"].sum()
    print(f"Totaal opbrengst: {Totaal_df}, Totaal referentie: {Totaal_ref}")
    factor = Totaal_ref / Totaal_df
    
    Nieuwe_ref = ref_data[["Verbruik"]] / factor
    Nieuwe_ref.set_index(ref_data.index, inplace=True)
    return Nieuwe_ref 

def plot_opbrengst_per_dag(df, verbruik=0, terugleverlimiet=False, afnamelimiet=False):
    print("Plotting daily data...")

    # Laad het logo
    logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")

    # Maak figuur en axes
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot data
    ax.plot(df.index, df['opbrengst1_W'] + df['opbrengst2_W'], label='Totale Opbrengst (kWh)', color='green')
    ax.plot(df.index, df['opbrengst1_W'], label='Opbrengst Paneel 1 (kWh)', color='blue')
    ax.plot(df.index, df['opbrengst2_W'], label='Opbrengst Paneel 2 (kWh)', color='orange')

    if isinstance(verbruik, type(df)) and len(verbruik['Verbruik']) == len(df['opbrengst1_W']):
        print("Verbruik is een DataFrame")
        verbruik = verbruik.copy()
        verbruik.set_index(df.index, inplace=True)
        ax.plot(df.index, verbruik["Verbruik"], label='Verbruik (kWh)', color='red')
        verschil = verbruik["Verbruik"] - df['opbrengst1_W'] - df['opbrengst2_W']
        ax.plot(df.index, verschil, label='Verschil (kWh)', color='purple')

    if terugleverlimiet:
        ax.axhline(y=terugleverlimiet, color='red', linestyle='--', label='Terugleverlimiet (kWh)')
    if afnamelimiet:
        ax.axhline(y=afnamelimiet, color='blue', linestyle='--', label='Afnamelimiet (kWh)')

    ax.set_title('Zonnepaneel Opbrengst per Kwartier over een dag')
    ax.set_xlabel('Datum en Tijd')
    ax.set_ylabel('Opbrengst (kWh)')
    ax.legend()
    ax.grid()

    # Voeg logo toe
    logo_ax = fig.add_axes([0.72, -0.1, 0.18, 0.18], anchor='NE', zorder=1)
    logo_ax.imshow(logo)
    logo_ax.axis('off')

    # Toon figuur in Streamlit
    st.pyplot(fig)


def plot_opbrengst_jaar(df, verbruik=0):
    print("Plotting yearly data...")        

    # Laad het logo
    logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")

    # Maak figuur en axes
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot data
    ax.plot(df.index, df['opbrengst1_W'] + df['opbrengst2_W'], label='Totale Opbrengst (kWh)', color='green')
    ax.plot(df.index, df['opbrengst1_W'], label='Opbrengst Paneel 1 (kW)', color='blue')
    ax.plot(df.index, df['opbrengst2_W'], label='Opbrengst Paneel 2 (kW)', color='orange')

    if isinstance(verbruik, type(df)) and len(verbruik['Verbruik']) == len(df['opbrengst1_W']):
        verbruik = verbruik.copy()
        verbruik.set_index(df.index, inplace=True)
        ax.plot(df.index, verbruik["Verbruik"], label='Verbruik (kWh)', color='red')
        ax.plot(df.index, verbruik["Verbruik"] - df['opbrengst1_W'] - df['opbrengst2_W'], label='Verschil (kWh)', color='purple')
    else:
        print(type(verbruik))
        print(type(df))
        print(f'Verbruik lengte: {verbruik.shape} Lengte df: {df.shape}')

    ax.set_title('Zonnepaneel Opbrengst per Kwartier over een jaar')
    ax.set_xlabel('Datum en Tijd')
    ax.set_ylabel('Opbrengst (kW)')
    ax.legend()
    ax.grid()

    # Voeg logo toe in aparte axes met jouw gewenste positie
    logo_ax = fig.add_axes([0.72, -0.1, 0.18, 0.18], anchor='NE', zorder=1)
    logo_ax.imshow(logo)
    logo_ax.axis('off')  # Geen assen rondom logo

    # Toon figuur in Streamlit
    st.pyplot(fig)
    

def plot_opbrengst_dag(df, verbruik, dag: str, ):
    dag = pd.to_datetime(dag, format="%d-%m-%Y").date()
    dag_df = df[f"{dag} 00:00": f"{dag} 23:45"]
    dag_verbruik = verbruik[f"{dag} 00:00": f"{dag} 23:45"]

    # Laad het logo
    logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")

    # Maak figuur
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dag_df.index, dag_df['opbrengst1_W'], label='Opbrengst Paneel 1 (kWh)', color='blue')
    ax.plot(dag_df.index, dag_df['opbrengst2_W'], label='Opbrengst Paneel 2 (kWh)', color='orange')
    ax.plot(dag_df.index, dag_df['opbrengst1_W'] + dag_df['opbrengst2_W'], label='Totale Opbrengst (kWh)', color='green')
    ax.plot(dag_verbruik.index, dag_verbruik["Verbruik"], label='Verbruik (kWh)', color='red')
    ax.plot(dag_verbruik.index, dag_verbruik["Verbruik"] - dag_df['opbrengst1_W'] - dag_df['opbrengst2_W'], label='Verschil (kWh)', color='purple')

    ax.set_title(f'Zonnepaneel Opbrengst op {dag}')
    ax.set_xlabel('Tijd')
    ax.set_ylabel('Opbrengst (kWh)')
    ax.legend()
    ax.grid()

    # Voeg logo toe in een aparte as (rechtsboven)
    logo_ax = fig.add_axes([0.72, -0.10, 0.18, 0.18], anchor='SE', zorder=1)
    logo_ax.imshow(logo)
    logo_ax.axis('off')  # Geen assen bij het logo

    # Berekening teruglevering/afname
    totaal_terugleveren = 0
    totaal_afnemen = 0
    for i in range(0, len(dag_df)):
        verschil = dag_df["opbrengst1_W"].iloc[i] + dag_df["opbrengst2_W"].iloc[i] - dag_verbruik["Verbruik"].iloc[i]
        if verschil > 0:
            totaal_terugleveren += verschil
        else:
            totaal_afnemen += -verschil

    # Streamlit output
    st.pyplot(fig)
    st.write(f"🔋 **Totaal terug geleverd:** {totaal_terugleveren:.2f} kWh")
    st.write(f"⚡ **Totaal afgenomen:** {totaal_afnemen:.2f} kWh")
    
def plot_heatmap(df):
    plt.clf()
    plt.figure(figsize=(12, 6))
    heatmap_data = df.pivot_table(index=df.index.date, columns=df.index.time, values='opbrengst1_W')
    sns.heatmap(heatmap_data, cmap='YlGnBu', cbar_kws={'label': 'Verbruik (kW)'})

    
    plt.title('Zonnepaneel Opbrengst Heatmap')  



def plot_energie_per_maand(df):
    plt.clf()
    plt.figure(figsize=(12, 6))
    maand_opbrengst = df['opbrengst1_W'].resample('M').sum()
    maand_opbrengst.plot(kind='bar')
    plt.title('Maandelijkse Opbrengst Paneel 1 (W)')
    plt.xlabel('Maand')
    plt.ylabel('Opbrengst (W)')
    plt.grid()
    plt.show()

def plot_prognose(df):
    plt.clf()
    plt.figure(figsize=(12, 6))
    df['opbrengst1_W'].plot(label='Opbrengst Paneel 1 (W)', color='blue')
    df['opbrengst2_W'].plot(label='Opbrengst Paneel 2 (W)', color='orange')
    plt.title('Voorspelling Zonnepaneel Opbrengst')
    plt.xlabel('Datum en Tijd')
    plt.ylabel('Opbrengst (W)')
    plt.legend()
    plt.grid()
    plt.show()

def plot_energiebalans(df):
    plt.clf()
    plt.figure(figsize=(12, 6))
    df['opbrengst1_W'].plot(label='Opbrengst Paneel 1 (W)', color='blue')
    df['opbrengst2_W'].plot(label='Opbrengst Paneel 2 (W)', color='orange')
    plt.title('Energiebalans Zonnepaneel')
    plt.xlabel('Datum en Tijd')
    plt.ylabel('Opbrengst (W)')
    plt.legend()
    plt.grid()
    plt.show()

def maak_heatmap_verbruik(df, verbruik_col:str="Verbruik", limiet:int=40000):
    # Zorg dat index datetime is
    df.index = pd.to_datetime(df.index)

    # Bereken % benutting per kwartier
    df["%_benut"] = df / (limiet/96) * 100

    # Groepeer per dag: gemiddelde % benutting per dag
    dag_data = df["%_benut"].resample("D").mean()

    # Maak nieuwe kolommen: dagnummer en maandnaam
    heatmap_df = dag_data.to_frame(name="benutting")
    heatmap_df["dag"] = heatmap_df.index.day
    heatmap_df["maand"] = heatmap_df.index.month_name()

    # Zet in pivotvorm: rijen = maand, kolommen = dag
    pivot = heatmap_df.pivot_table(
        index="maand",
        columns="dag",
        values="benutting",
        aggfunc="mean"
    )

    # Zorg dat maanden in logische volgorde staan
    maanden_volgorde = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    pivot = pivot.reindex(maanden_volgorde)

    # Laad het logo
    logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")

    # Maak figuur en axes
    fig, ax = plt.subplots(figsize=(16, 8))

    # Plot heatmap in deze axes
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="RdYlGn_r", vmin=0, vmax=100,
                linewidths=0.5, linecolor='gray', ax=ax)

    ax.set_title("Gemiddeld % benut vermogen per dag", fontsize=16)
    ax.set_xlabel("Dag van de maand")
    ax.set_ylabel("Maand")

    plt.tight_layout()

    # Voeg logo toe in aparte axes
    logo_ax = fig.add_axes([0.72, -0.1, 0.18, 0.18], anchor='NE', zorder=1)
    logo_ax.imshow(logo)
    logo_ax.axis('off')

    # Bepaal dag met hoogste benutting
    max_benutting = dag_data.max()
    max_dag = dag_data.idxmax()  # datetime van die dag
    #plot heatmap in python
    plt.show
    # Print met Streamlit
    st.pyplot(fig)
    st.write(f"📅 **Dag met hoogste afname:** {max_dag.date()} met gemiddeld {max_benutting:.2f}% benutting")
    

test = KwartierdataProcessor(
    aantal_jaren=1,
    breedtegraad=52.13,
    lengtegraad=6.54,
    hellingshoek1=45,
    hellingshoek2=45,
    orientatie1="oost",
    orientatie2="west",
    wp1=450,
    wp2=300,
    begin_dag = '2023-01-01',
    zonnedata_pos=True,
    rendement=0.95,
    omvormer=3,
).bereken_kwartieropbrengst()
print(test["2023-06-06 00:15":"2023-06-06 23:30"])
#maak_heatmap_verbruik(test, verbruik_col="Opbrengst", limiet=40000)

""""
teruglever_limiet = -2 #kWh per dag
afname_limiet =     5 #kWh per dag
pos_neg_opwek = -1 # -1 voor negatief, 1 voor positief

verbruik = read_data("C:\\Users\LuukTijhaar(bind)\\Downloads\\2024 Export-voor-Luuk-20250224-1217.xlsx")
print(verbruik.head())

verbruik = normaliseer_data(test, verbruik)
print(verbruik.head())
dag_data_verbruik = kwartierdata_naar_dagdata(verbruik)

dag_data = kwartierdata_naar_dagdata(test)
dag_data_verbruik = kwartierdata_naar_dagdata(verbruik)


kopie_dag = dag_data_verbruik.copy()
kopie_dag.set_index(dag_data.index, inplace=True)
verschil_dag_basis = kopie_dag["Verbruik"] - (dag_data['opbrengst1_W'] + dag_data['opbrengst2_W'])

kopie = verbruik.copy()
kopie.set_index(test.index, inplace=True)
verschil_per_kwartier = kopie["Verbruik"] - test['opbrengst1_W'] - test['opbrengst2_W']
plot_opbrengst_per_dag(dag_data, dag_data_verbruik, terugleverlimiet=teruglever_limiet, afnamelimiet=afname_limiet)

plot_opbrengst_jaar(test, verbruik)"""
#plot_opbrengst_dag(test, "01-06-2023")
#plot_heatmap(test)
#plot_belastingduurkromme(test)

#st.write(test)