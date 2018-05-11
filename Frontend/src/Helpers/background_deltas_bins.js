// deltaQT Database - Background Distribution, Updated July 18, 2017 
// 
// Copyright (C) 2017, Tatonetti Lab
// Tal Lorberbaum <tal.lorberbaum@columbia.edu>
// Victor Nwankwo <vtn2106@cumc.columbia.edu>
// Nicholas P. Tatonetti <nick.tatonetti@columbia.edu>
// All rights reserved.
// 
// Released under a CC BY-NC-SA 4.0 license.
// For full license details see LICENSE.txt at 
// https://github.com/tal-baum/deltaQTDb or go to:
// http://creativecommons.org/licenses/by-nc-sa/4.0/

const background_deltas_MF = {"min": -113, "max": 150,
"bins": [{"x0": -110, "x1": -100, "value": 0.001744},
{"x0": -100, "x1": -90, "value": 0.006103},
{"x0": -90, "x1": -80, "value": 0.009590},
{"x0": -80, "x1": -70, "value": 0.012206},
{"x0": -70, "x1": -60, "value": 0.024411},
{"x0": -60, "x1": -50, "value": 0.060156},
{"x0": -50, "x1": -40, "value": 0.118568},
{"x0": -40, "x1": -30, "value": 0.273753},
{"x0": -30, "x1": -20, "value": 0.748897},
{"x0": -20, "x1": -10, "value": 1.817754},
{"x0": -10, "x1": 0, "value": 4.152500},
{"x0": 0, "x1": 10, "value": 27.610678},
{"x0": 10, "x1": 20, "value": 19.339680},
{"x0": 20, "x1": 30, "value": 13.481892},
{"x0": 30, "x1": 40, "value": 9.307597},
{"x0": 40, "x1": 50, "value": 6.454988},
{"x0": 50, "x1": 60, "value": 4.405329},
{"x0": 60, "x1": 70, "value": 3.093233},
{"x0": 70, "x1": 80, "value": 2.256281},
{"x0": 80, "x1": 90, "value": 1.664313},
{"x0": 90, "x1": 100, "value": 1.292916},
{"x0": 100, "x1": 110, "value": 1.054907},
{"x0": 110, "x1": 120, "value": 0.884902},
{"x0": 120, "x1": 130, "value": 0.752384},
{"x0": 130, "x1": 140, "value": 0.591969},
{"x0": 140, "x1": 150, "value": 0.582379},
]};

const background_deltas_M = {"min": -106, "max": 150,
"bins": [{"x0": -110, "x1": -100, "value": 0.003475},
{"x0": -100, "x1": -90, "value": 0.001737},
{"x0": -90, "x1": -80, "value": 0.005212},
{"x0": -80, "x1": -70, "value": 0.010424},
{"x0": -70, "x1": -60, "value": 0.022586},
{"x0": -60, "x1": -50, "value": 0.060809},
{"x0": -50, "x1": -40, "value": 0.112932},
{"x0": -40, "x1": -30, "value": 0.180690},
{"x0": -30, "x1": -20, "value": 0.644578},
{"x0": -20, "x1": -10, "value": 1.501121},
{"x0": -10, "x1": 0, "value": 3.469604},
{"x0": 0, "x1": 10, "value": 27.306844},
{"x0": 10, "x1": 20, "value": 19.427698},
{"x0": 20, "x1": 30, "value": 13.452751},
{"x0": 30, "x1": 40, "value": 9.361155},
{"x0": 40, "x1": 50, "value": 6.664698},
{"x0": 50, "x1": 60, "value": 4.651042},
{"x0": 60, "x1": 70, "value": 3.276752},
{"x0": 70, "x1": 80, "value": 2.420210},
{"x0": 80, "x1": 90, "value": 1.787793},
{"x0": 90, "x1": 100, "value": 1.419462},
{"x0": 100, "x1": 110, "value": 1.136265},
{"x0": 110, "x1": 120, "value": 0.955574},
{"x0": 120, "x1": 130, "value": 0.835693},
{"x0": 130, "x1": 140, "value": 0.655003},
{"x0": 140, "x1": 150, "value": 0.635891},
]};

const background_deltas_F = {"min": -113, "max": 150,
"bins": [{"x0": -110, "x1": -100, "value": 0.000000},
{"x0": -100, "x1": -90, "value": 0.010500},
{"x0": -90, "x1": -80, "value": 0.013999},
{"x0": -80, "x1": -70, "value": 0.013999},
{"x0": -70, "x1": -60, "value": 0.026249},
{"x0": -60, "x1": -50, "value": 0.059498},
{"x0": -50, "x1": -40, "value": 0.124245},
{"x0": -40, "x1": -30, "value": 0.367486},
{"x0": -30, "x1": -20, "value": 0.853968},
{"x0": -20, "x1": -10, "value": 2.136670},
{"x0": -10, "x1": 0, "value": 4.840318},
{"x0": 0, "x1": 10, "value": 27.916703},
{"x0": 10, "x1": 20, "value": 19.251028},
{"x0": 20, "x1": 30, "value": 13.511243},
{"x0": 30, "x1": 40, "value": 9.253653},
{"x0": 40, "x1": 50, "value": 6.243766},
{"x0": 50, "x1": 60, "value": 4.157844},
{"x0": 60, "x1": 70, "value": 2.908391},
{"x0": 70, "x1": 80, "value": 2.091172},
{"x0": 80, "x1": 90, "value": 1.539942},
{"x0": 90, "x1": 100, "value": 1.165456},
{"x0": 100, "x1": 110, "value": 0.972964},
{"x0": 110, "x1": 120, "value": 0.813719},
{"x0": 120, "x1": 130, "value": 0.668475},
{"x0": 130, "x1": 140, "value": 0.528480},
{"x0": 140, "x1": 150, "value": 0.528480},
]};

const all = {
  background_deltas_F,
  background_deltas_M,
  background_deltas_MF
};

export default all;
export {
  background_deltas_F,
  background_deltas_M,
  background_deltas_MF
};