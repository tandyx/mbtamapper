/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module shapes
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { * } from "sorttable/sorttable.js"
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, VehicleProperty, RealtimeLayerOnClickOptions, NextStop } from "../types/index.js"
 * @import { Layer, Realtime } from "leaflet";
 * @import { BaseRealtimeLayer } from "./base.js"
 * @exports VehicleLayer
 */

"use strict";

/**
 * encapsulating class to plot Vehicles on a leaflet map
 * after object creation, you can call `.plot` to plot it
 */
class VehicleLayer extends BaseRealtimeLayer {
  static #hex_css_map = {
    FFC72C:
      "filter: invert(66%) sepia(78%) saturate(450%) hue-rotate(351deg) brightness(108%) contrast(105%);",
    "7C878E":
      "filter: invert(57%) sepia(2%) saturate(1547%) hue-rotate(160deg) brightness(91%) contrast(103%);",
    "003DA5":
      "filter: invert(13%) sepia(61%) saturate(5083%) hue-rotate(215deg) brightness(96%) contrast(101%);",
    "008EAA":
      "filter: invert(40%) sepia(82%) saturate(2802%) hue-rotate(163deg) brightness(88%) contrast(101%);",
    "80276C":
      "filter: invert(20%) sepia(29%) saturate(3661%) hue-rotate(283deg) brightness(92%) contrast(93%);",
    "006595":
      "filter: invert(21%) sepia(75%) saturate(2498%) hue-rotate(180deg) brightness(96%) contrast(101%);",
    "00843D":
      "filter: invert(31%) sepia(99%) saturate(684%) hue-rotate(108deg) brightness(96%) contrast(101%);",
    DA291C:
      "filter: invert(23%) sepia(54%) saturate(7251%) hue-rotate(355deg) brightness(90%) contrast(88%);",
    ED8B00:
      "filter: invert(46%) sepia(89%) saturate(615%) hue-rotate(1deg) brightness(103%) contrast(104%);",
    ffffff:
      "filter: invert(100%) sepia(93%) saturate(19%) hue-rotate(314deg) brightness(105%) contrast(104%);",
  };

  /**@type {((event: L.LeafletMouseEvent) => void)[]} */
  static onClickArry = [];

  /**
   * string or html element of vehicle
   * @param {VehicleProperty} properties from geojson
   * @returns {L.DivIcon}
   */
  #getIcon(properties) {
    const delayClassName = getDelayClassName(properties?.next_stop?.delay || 0);
    const delayStyle =
      (properties?.next_stop?.delay || 0) < 5 * 60
        ? ""
        : `text-decoration: underline 2px var(--vehicle-${delayClassName});
        -webkit-text-decoration-line: underline;
        -webkit-text-decoration-color: var(--vehicle-${delayClassName});
        -webkit-text-decoration-thickness: 2px;
        text-decoration-thickness: 2px;
      `;
    // src="/static/img/icon.png"
    const iconHtml = /* HTML */ `
      <div class="vehicle_wrapper">
        <img
          src="data:image/png;base64,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zZDuvffetABJdfX3hBcsWFBtueWW6fXT4y0PAACgNW8s/TjyIN5z1Xd0PvLII6u77rorLTzSc9Wni/CFAQAANG6n0r9GHsB7qvoGR4cffni1fPnytOBIL6b/WIT76NLoRQEAADTmwOiD5XfOnDnVsmXL0kIjvZzq7wjPmzdv+PvjI19rPdji0tgAAABekVNKT0UeuHummTNnVosXL04LjNREK1asqN71rncN30F85Guvx7qntHkAAAAvywWlZyMP2j3R1KlTq3POOadav359WlqkpvviF79YvfnNb06vwx7ra6XXBQAA8KKNL30h8nDdE9U3uDruuOOqNWvWpCVFartLLrmk2nrrrdPrsoeqn9G9RwAAAC9ocmlV5KG6J9p1112rW2+9NS0lUiervx98/PHHD990beRrtEf6fmn/AAAAntfU0iORh+mut+mmm1YLFy6sNmzYkJYRqVvdeOON1axZs9LrtUd6svQrAQAAJFuWvhp5iO56s2fP9jxf9Wz1d9A//OEPV5MmTUqv3R6ofm73kQEAAPxfryl9PfLw3NWmTZtWfeYzn0kLh9SL3XnnndXee++dXsc90E9LJwYAABDblP4i8tDc1epn+q5atSotGVKv97GPfayaMGFCek13uWdK8wMAAEax7UvfjDwsd62JEydWixYtSkuF1E/dfvvt1Y477phe312ufqTZ2QEAAKNQvfx+J/KQ3LXqhWHZsmVpmZD6sccff7x673vf24t3il4QAAAwitSXPX8z8mDcleoF4dRTTx1eGEYuEVK/d91111UzZsxIr/suVn8S7HJoAABGhfqGVz3znd8tt9yyWrJkSVoapEHqoYceGv5e+8jXfxervxN8UgAAwACrH3X0x5GH4a60++67V/fee29aFqRB7IknnqjOPPPMXrokur47tEckAQAwkKZGDz3nd+7cuS551qhs8eLF1fTp09N7okvVzwn+lQAAgAEyufRI5OG349WPh7nwwgvTUiCNpu65555qt912S++PLvVkaf8AAIABML60MvLQ2/HqGwEtXbo0LQPSaKy+AuLoo49O75Mu9f3SHgEAAH3uC5GH3Y63xx57VKtXr05LgDTaW7hwYa98L/jbpdcHAAD0qQsiD7kd79BDD63WrVuXBn9JG7viiiuqSZMmpfdOF/paafMAAIA+c0psfN7nyAG3o82bN2/47rcjB35JP9/NN99cvfrVr07voS50b2lsAABAnziw9FTkwbZjjR07trrgggvSkC/p+bv77rurHXbYIb2futDiAACAPrBT6XuRB9qONXny5Oqqq65Kw72kF27t2rXV3nvvnd5XXWhBAABAD9uq9I3Ig2zHqp9vesstt6ShXtKL77HHHqsOPvjg9P7qcM+Ufj0AAKAH1Y87ejjyENux6u8v3n777WmYl/TS27BhQ3XYYYel91mHq58RvHsAAECP+Xzk4bVj1c/4Xb58eRriJb386iW4B54V/JelaQEAAD3ipMhDa8faZptthm/eM3J4l9RMp5xySnrfdbgvl8YEAAB0WX15Yn2Z4siBtSNtv/321cqVK9PALqnZ3v/+96f3X4dbFAAA0EXTS38VeVDtSPXyu3r16jSoS2qnLi/BT5cOCQAA6IKh0t2Rh9SOVF/27JNfqfN1+XLofyy9LgAAoMM+FXk47Uj1Da9851fqXl2+MdZjpU0CAAA6ZE5svBxx5GDaevWjjtztWepuPfCIpCsCAAA6oH4cyd9GHkhbb/r06dVtt92WhnFJna9egg8++OD0Pu1Qz5R+OQAAoGW3Rh5GW2+zzTarbrnlljSES+pejz32WLX33nun92uH+lZsvBEfAAC04tTIQ2jrjRs3rrrqqqvS8C2p+61du7baYYcd0vu2Q9U/kAMAgMbNLH0/8gDaep/85CfT0C2pd6pvSld/P3/ke7dDnRQAANCgsaV1kQfP1ps3b14atiX1XjfffHM1adKk9B7uQP9S2iYAAKAhn448dLbeoYceWj3xxBNp0JbUm11xxRXV0NBQei93oAdj47PJAQDgFXlz6SeRB85W22OPPap169alAVtSb7dw4cL0fu5QCwIAAF6B+tLnJyIPmq02Y8aMas2aNWmwltQfHXPMMel93YF+WNo2AADgZVoYechstQkTJlRLly5NA7Wk/ql+PNJuu+2W3t8d6J4AAICXYbvY+InKyAGz1S688MI0TEvqv+65555q+vTp6T3egY4LAAB4iVZGHixbbe7cuWmIltS/LV68uBs3xfr70rQAAIAX6bTIQ2Wr7b777sOXTY4coCX1d2eeeWZ6v3eg/y8AAOBF2Kr03cgDZWttueWW1b333psGZ0n9X/0oszlz5qT3fcs9U9o3AADgBXwx8jDZWvXlkUuWLElDs6TB6cEHHxy+u/vI93/Lfb00PgAA4Hm8IzZ+cjJykGytU089NQ3Lkgav6667rhvfB/ZsYAAAntOY0mORB8jW2nHHHX3vVxpFnX766ekcaLnvlbYMAAAY4aTIw2NrTZw4sVq2bFkakCUNbo8//vjwD75Gngctd2UAAMDPmFz6VuTBsbUWLVqUhmNJg9/tt99eTZgwIZ0JLfaT0psCAAD+3UWRh8bWqu8IO3IoljR6+tjHPpbOhZb7cgAAQLFN6UeRB8ZWmj59erVq1ao0EEsaPdWPRtp7773T+dByBwUAAKPeH0YeFFvrM5/5TBqGJY2+7rzzzmrSpEnpjGix/1IaCgAARq23lJ6NPCi20uzZs9MQLGn09uEPfzidEy13WgAAMGrV34sbOSC20qabblrdddddaQCWNHpbv3599aY3vSmdFy3216VxAQDAqPP26OCnvwsXLkzDryTdeOON1dDQUDozWmxeAAAw6twbeTBspV133bXasGFDGnwlqe74449P50aL+RQYAGCU2TfyUNhK48aNq2699dY08ErSf7R27dpqq622SudHi50eAACMGmsiD4StdNxxx6VhV5JGdskll6Tzo8X+KnwKDAAwKtTPwhw5DLbS1KlTqzVr1qRBV5Keq7e85S3pHGkxnwIDAIwCayMPgq10zjnnpAFXkp6vL37xi9WYMWPSWdJSPgUGABhwe0ceAltp5syZw484GTngStIv6l3velc6T1rs1AAAYGDdHnkAbKWrrroqDbaS9EKtWLGimjBhQjpTWuq/BQAAA2lm6enIA2DjzZkzJw21kvRimzdvXjpXWqy+LwIAAAPm9yMPfo03NDRULVu2LA20kvRiqx+LtMUWW6TzpaXuDAAABsoWpR9GHvwa7/DDD0/DrCS91BYuXJjOl5Z6prR9AAAwMM6LPPQ13rhx46rly5enQVaSXmqPPvpo9apXvSqdMy1VXyEDAMAAmFD6TuSBr/GOPPLINMRK0sttwYIF6ZxpqR+UpgUAAH3vtMjDXuONHz9++O6tIwdYSXq5dfhT4I8GAAB979HIg17jzZ07Nw2vkvRK6+CnwN8sDQUAAH1rl8hDXuPVz+y855570uAqSa+0+lPgLbfcMp07LXVoAADQt3438oDXeEcddVQaWiWpqc4+++x07rTUfw4AAPpSffOr70Ye8Bqtfu7vHXfckQZWSWqq+rnAm222WTp/WujHsfGxcQAA9JkTIg93jTdnzpw0rEpS05100knp/GmpDwYAAH1nTeTBrvGuvfbaNKhKUtPdeeedw1ecjDyDWui/BAAAfWX70rORB7tG22WXXdKQKkltdfDBB6dzqKX2CAAA+sbnIg90jfe5z30uDaiS1FbXXXddOoda6vMBAEBfGFP6m8gDXaPNmDGj2rBhQxpQJanNdt5553QetVB9A8H6RoIAAPS4d0Qe5hrvAx/4QBpMJantLrroonQetdS7AwCAnnd55EGu0caNG1fdd999aTCVpLZbt25dNWXKlHQutdAfBAAAPa2+/PnvIg9yjXbggQemoVSSOtXcuXPTudRC/1waHwAA9Kx9Iw9xjXfllVemgVSSOtVNN92UzqWWOjQAAOhZV0Ye4Bpt6623dvMrSV1v1qxZ6XxqoWsDAICeNFT6duQBrtHmz5+fBlFJ6nQLFy5M51ML/VNpXAAA0HMOiDy8NdrQ0FC1YsWKNIhKUqd74IEHqk022SSdUy10SAAA0HOuiDy4Ndqee+6ZhlBJ6laHHHJIOqdaaEkAANBz/jTy4NZo5557bhpAJalbXXrppemcaqH/GQAA9JRtIw9tjTZ27Nhq5cqVaQCVpG71yCOPVJMmTUrnVQvtGgAA9IwzIg9sjbbXXnul4VOSul2HLoNeEAAA9IwvRx7YGu38889Pg6ckdbuLL744nVctdF8AANATNin9IPLA1ljjxo2rVq9enQZPSep2a9eu7cTdoH9UmhgAAHTdwZGHtUabPXt2GjolqVc64IAD0rnVQu8MAAC67rLIg1qjnXfeeWnglKRe6aKLLkrnVgvVZy0AAF32tciDWqOtWLEiDZyS1CutWbOmGhoaSmdXw9VnLQAAXTS99EzkQa2xZs6cmYZNSeq1dt1113R+NdyzpdcEAABdc1jkIa3RTj755DRoSlKv9b73vS+dXy10dAAA0DWfjTygNdrixYvToClJvdZ1112Xzq8W+p0AAKBrHoo8oDXWpEmTqsceeywNmpLUa61fv77abLPN0jnWcI8GAABdMb70ZOQBrbHmzJmThkxJ6tUOOuigdI413L/FxmevAwDQYXtFHs4a7ZxzzkkDpiT1aosWLUrnWAu9IwAA6LizIw9mjbZ06dI0YEpSr3bHHXekc6yFPhIAAHTcssiDWWPV36XbsGFDGjAlqZfbYost0nnWcP85AADouG9FHswaa5999kmDpST1evW9C0aeZw33dwEAQEdtEXkoa7QzzjgjDZaS1OudddZZ6TxrodcEAAAdc0DkgazRlixZkgZLSer1rrnmmnSetdAvBwAAHfPByANZY40dO7Z6+OGH02ApSb3eI488MnyGjTzXGs6NsAAAOuiayANZY+28885pqJSkfmmnnXZK51rDXRcAAHTM45EHssY65phj0kApSf3Ssccem861hqvPYAAAOmCo9MPIA1ljnXvuuWmglKR+6ZOf/GQ61xruB6UxAQBA67aPPIw12vXXX58GSknql77whS+kc62FtgsAAFp3VORBrLHGjBlTPfTQQ2mglKR+ae3atdXQ0FA63xruiAAAoHXnRR7EGmvGjBlpmJSkfqs+y0aebw23KAAAaF2rd4CeM2dOGiQlqd+qz7KR51vD3RAAALRuVeRBrLHmzZuXBklJ6rdOP/30dL413OoAAKB1fxl5EGusiy++OA2SktRv/dZv/VY63xrurwMAgFbVj0B6KvIg1lg33XRTGiQlqd9aunRpOt8arj6L6zMZAICWvD7yENZoq1evToOkJPVbDz74YDrfWuh1AQBAa/aPPIA11uTJk9MQKUn92uabb57OuYbbLwAAaM0pkQewxtphhx3SAClJ/dqsWbPSOddwJwUAAK25IPIA1lgHHHBAGiAlqV+rz7SR51zD1c9lBwCgJVdHHsAa64QTTkgDpCT1a8cff3w65xquPpMBAGjJlyIPYI21YMGCNEBKUr929tlnp3Ou4f4oAABozUORB7DGuuyyy9IAKUn92qWXXprOuYZbGwAAtOaPIw9gjXX99denAVKS+rUbbrghnXMN9/UAAKA1fx95AGusZcuWpQFSkvq1O+64I51zDVefyQAAtOQnkQewxnrggQfSAClJ/drq1avTOddwTwUAAK2YEnn4aqyhoaFqw4YNaYCUpH6tPtPqs23keddw9dkMAEDDZkYevBprypQpaXiUpH6vPttGnncNt20AANC4t0cevBprm222SYOjJPV79dk28rxruD0DAIDGvTPy4NVYu+++exocJanf22233dJ513D12QwAQMPeHXnwaqz99tsvDY6S1O/tu+++6bxruCMCAIDGHRV58Gqsgw8+OA2OktTvHXLIIem8a7ijAwCAxn0g8uDVWIceemgaHCWp3/vVX/3VdN413IkBAEDj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RqXJpX+IPCC20pQpU6qVK1emAVjS6G327NnprGix+tPftwQAAKPWByMPia11yCGHpAFY0ujsM5/5TDojWu4PAwCAUW1c6euRB8XWuuyyy9IgLGl0tWrVqmr69OnpfGixH5W2CQAARr1fjjwstta0adOq++67Lw3EkkZPc+bMSWdDy9V3vgcAgGF/FHlgbK299tqreuKJJ9JQLGnwW7RoUToTWu5bsfGeBwAAMGxm6ceRB8fW+tCHPpQGY0mD3bJly6qJEyem86DlTgoAABjh4siDY2uNHz++uummm9KALGkwe+yxx6odd9wxnQUt91hpTAAAwAiblb4deYBsrTe84Q3Vww8/nAZlSYPXqaeems6Alnum9I4AAIDncUrkIbLV3vOe96RBWdJgtWTJkmpoaCi9/1vuiwEAAL9AfangA5EHyVa74IIL0sAsaTC69957qy233DK971vuu6WtAgAAXkB9Q6wnIw+UrbXJJptUN954YxqcJfV39fd+d9999/Se70CnBQAAvEgLIg+Urfaa17ymWrVqVRqgJfVvc+fOTe/1DrQyAADgJRgqrY88WLba2972tmrDhg1piJbUf1144YXpPd6BfljaLgAA4CXarfRU5AGz1U466aQ0SEvqr5YuXVpNmDAhvb870MIAAICX6cLIA2brffazn00DtaT+aM2aNdWMGTPS+7oDPVEaGwAA8DJtUvp65EGz1eqbYl133XVpsJbU261bt67aY4890nu6A/2k9OYAAIBX6O2xcbgcOXC22tSpU6s77rgjDdiSerMnnniiOvTQQ9N7uUN9OgAAoCHnRh44W++1r31ttXLlyjRoS+q95s2bl97DHWpduPQZAIAG1XeFXh158Gy9XXbZpXrkkUfSsC2pd/rkJz+Z3rsd6vux8dnlAADQqNeWvht5AG29Aw880OORpB7tqquuqsaNG5fetx3q1AAAgJb8euQBtCMdffTRafCW1N1uueWWarPNNkvv1w51awAAQMuujjyIdqRTTjklDeCSutNtt91WTZ8+Pb1PO9TflqYFAAC0bNPSn0YeSDvS+973vjSIS+psy5cvr1796len92eHero0JwAAoEN2Lz0ZeTDtSGeddVYayCV1prvvvruaMWNGel92sE8FAAB02AmRB9OO9dGPfjQN5pLarX4s2TbbbJPejx3s7th4V3oAAOi4KyIPqB1pzJgx1fnnn58GdEnttHr16mr77bdP78UO9lel6QEAAF0yrvRg5EG1I9VL8Mc+9rE0qEtqtvqT3y4vv/VXLuqvXgAAQFe9uvR3kQfWjnXmmWemgV1SM9Xf+e3yZc91JwUAAPSIt5f+LfLQ2rFOPfXUNLhLemXVd3vu8g2v6j4fAADQY+ZFHlw72jHHHFNt2LAhDfGSXnq33357Nx919B89XBofAADQgy6PPMB2tMMOO8wSLL3Cbrnllmr69Onp/dXhvlHaKgAAoEfVjye5PfIg29Fmz55drV27Ng31kl64q666qpo8eXJ6X3W475V2CgAA6HETS49EHmg72g477FDdc889abiX9PxdcMEF1dixY9P7qcM9VTowAACgT2xZ+ovIg21Hq7+/ePPNN6chX9LP98QTT1Tz5s1L76Eu9GzplAAAgD7zxtI/Rh5wO9qmm25aXXHFFWngl7SxdevWVYceemh673SpCwIAAPrU3qUfRR5yO9rQ0FD10Y9+NA3+0mhv9erV1R577JHeM13qCwEAAH3uyNJPIw+7He+II46oHn300bQESKOxpUuX9sIzfv+jleFxRwAADIiTS89EHno73qxZs6o777wzLQPSaOrCCy+sJkyYkN4fXaq+ad7kAACAAfKbsfEGNyOH3443ZcqU6sorr0xLgTToPf7449XcuXPTe6KLfbU0NQAAYAB9KPIA3JXq7wXPnz+/2rBhQ1oSpEHs3nvvrXbffff0Xuhifxwb7xgPAAAD6+ORB+GuNXv27GrlypVpWZAGqSVLllRbbrllev13sfoxaa8JAAAYBS6MPBB3rS222KL6vd/7vbQ0SP1efcnzqaeeOnzFw8jXfRf7ZmmbAACAUeSyyINxVzv22GPdJVoD07Jly6odd9wxvc673HdK2wcAAIxCvxV5QO5q2223XXXLLbekZULqpxYtWlRNnDgxvb673DfD8gsAwCh3TuRBuauNHz+++tCHPuQGWeq7Vq1aVc2ZMye9pnug+ju/LnsGAIDiP0WPPCf4Z9tll12qP/zDP0xLhtSLfeYzn6mmTZuWXsc90NfDDa8AAODnnFz6aeThuauNGzeumjdvXrVu3bq0cEi90F133TV8N/ORr90eqX7Or0cdAQDAcziy9OPIQ3TX22abbaqrr746LR9St6ov0V+4cGG16aabptdrj/RIaWoAAADP652lH0YeprvemDFjqve85z3VmjVr0jIidbJbb7212nXXXdNrtIdaVZocAADAC3pr6duRh+qeaOrUqdXHP/5xN8lSx6t/+HLccccNX5o/8nXZQ32hND4AAIAX7XWlr0UernummTNnVosXL05LitR069evr84555zhH76MfB32UM+WLggAAOBl2bx0b+RBu6faf//9qzvuuCMtLVIT1T9kqX/YMvJ112M9VTolAACAV2RsaUnkgbunqi9JPfHEE6vVq1enBUZ6OS1btqxXn+k7su+VDgwAAKAxC6MHnxU8svqOvL/xG7/hRll62S1fvrw6/PDDq6GhofT66sG+UdopAACAxtWPSfp+5CG859p8882r97///dVXvvKVtOBIz1X9PN8jjzyy129w9bM9XNo6AACA1ryp9CeRh/GebMqUKdWZZ55ZrV27Ni08Ut29995bzZ07txo/fnx6/fRwny+NCwAAoHWblW6NPJT3bNOmTave9773VStXrkwLkEZnX/rSl6qjjz662mSTTdLrpYd7snRyAAAAHfeR0k8iD+k9W73s1Je53nbbbWkh0ujo2muvrQ444IBqzJgx6fXR4/1VafcAAAC6Zv/SdyIP6z3ffvvtVy1ZsiQtSBq8NmzYUF1yySXVzjvvnF4HfdLdpWkBAAB03S+VvhJ5aO+LZs2aVZ177rlumDWA3X///dVZZ51VzZgxI/2590lPlz5VGgoAAKBn1M8L/kT02SXRP9vEiROrd7/73dX111+fFin1T/WnvVdeeWV14IEH9tMdnZ+rvy3NCQAAoGe9vfQXkYf5vmq77barzj777OqBBx5IC5Z6s7vvvruaP39+tfXWW6c/zz6svsmcS54BAKAPTC5dE3mo77vqR+Psu+++1ac//WmXSPdg9V29Fy1aVO25557V0NBQ+vPrw+rnbJ8aAABA33lP6Z8iD/l9WX0H6Tlz5lQXXXSR5wp3sdWrV1ef+MQnqr322mtQlt7/aF1puwAAAPpWfYOseyIP+31dvQwfdNBBw58M1zdaGrmkqdlWrFhRnXfeedU+++zT79/rfa7q781/KjZ+jx4AABgAp5S+G3n4H4je9KY3VfPmzauuueaaav369WmB00tr3bp11eLFi6tTTjll+PvYI/97D1BPlN4SAADAwHlV6abIS8BANXny5OqQQw4Z/sTytttuS8udnrulS5dW55xzTrX//vtXkyZNSv9dB6wnSwvDp74AADDwfqX0jchLwUC2+eabDy91H/jAB4Y/IX700UfT8jfaevjhh6slS5ZUZ5xxRjV79uzhHxqM/O82wK0M3/UFAIBRZdPS75R+GnlBGOjq77Dusssu1bHHHlude+651Re+8IWBvqlWfffsG264YfjT3frfeaeddhq0m1e92P65dFoAAACj1p6lxyIvC6Ou1772tdUBBxww/F3iSy+9tLr55purNWvWpIWyV6vvznzTTTdVl1xySXX66acP3zF7xowZ6d9zFPZs6YulrQIAAKA4ufStyMvDqG+zzTarZs2aNbwcn3jiidXChQuryy+/vLr66qurL3/5y8PPwh25jDZdfafr5cuXD/8z63/2ggULqhNOOGH497TDDjuMtkuYX0r1D3f2CgAAgBHqy6I/HRtvEDRykdALNG3atOFPXN/61rdWe+65Z3XYYYdVRxxxxM81f/78n2vk/1//PfXfW/8a9a9V/5oj/zl6UdU/zKl/qAMAAPALvb50c2y8dHTkYiH1cj8qXRgbf5gDAADwou1dWhd5yZB6rfqHNUtL2wQAAMArcHjp/4+8dEi90J2lNwcAAECDfr30tcgLiNSN7iu9PQAAAFoypjS39CeRFxKpE60p7RsAAAAdMlQ6sfRnkRcUqY3Wlg4KAACALqk/ET6i9GDkhUV6pT1dWlZ6RwAAAPSQt8bGO/H+JPIiI72Uflj6fGlmAAAA9LD6OcKXl/535MVG+kX9fem80hYBAADQR6aUPlz6euRFR/rZ6udNn1baJAAAAPrc3qXrSk9GXn40Ovtu6XdLuwQAAMAA2rw0v7Qh8kKk0VH9GKMTShMCAABglHhzbLzRUf29z5FLkgarb5Y+V9o+AAAARrH6mcIHlpaU/iHy8qT+7O9i483Q6svfAQAAGGFs6eDSNaV/irxUqbf7dmz8VH+/AAAA4EUbV3pn6arSX0VettQb/Vls/KT3gNKYAAAA4BWrvz/6wdK94W7S3ewHpS+X3l/aNgAAAGjVxNKvxMbH6PxJ5CVNzfbfS78dGy9P96xeAACALppe+rXYuKQ9XPq3yEucXlz1p+sPlT5bOrw0NQAAAOhZ9aeU9d2HF5T+qPSdyIueNvY/S18qfaS0V2l8AAAA0Ne2KB1U+nBsvMv0E6UfRl4IB7X633VD6erSh2LjTavqT84BAAAYJd5UOqp0Xuna0qrSX5aejrxE9no/jY2/95Wxccmv/51+vTQrAAAA4Bd4fWn/0qmlC0o3lG4vPVj609LfRl5C26r+Z9X/zAdj4++h/r3Uv6dTYuPvsf69AgAAQKumxMZHAu1TOvDfqxfT00ZUL6yf+vfq/z3y/6//nvrvrat/rW1j468NAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8n/bggAAAAABAyP/XNQQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALhgtrcwWh/NMAAAAASUVORK5CYII="
          alt="vehicle"
          width="60"
          height="60"
          style="
            ${VehicleLayer.#hex_css_map[properties.route_color] || ""};
            transform: rotate(${properties.bearing}deg) translateZ(0);
            -webkit-transform: rotate(${properties.bearing}deg) translateZ(0);
          "
        />
        <span class="vehicle_text" style="${delayStyle}"
          >${properties.display_name}</span
        >
      </div>
    `;

    return L.divIcon({ html: iconHtml, iconSize: [10, 10] });
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interval = options.interval || 12500;
    super(options);
  }

  /**
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ..._this.options, ...options };
    /**@type {BaseRealtimeOnClickOptions<VehicleProperty>} */
    const onClickOpts = { _this, idField: "vehicle_id" };
    const realtime = L.realtime(options.url, {
      interval: options.interval,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      interactive: options.interactive,
      getFeatureId: (f) => f.id,
      /**@type {(f: GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty>, l: L.Layer) => void} */
      onEachFeature(f, l) {
        l.id = f.id;
        l.feature.properties.searchName = `${f.properties.trip_short_name} @ ${f.properties.route?.route_name}`;
        l.bindPopup(_this.#getPopupHTML(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.properties.label || f.id);
        l.setIcon(_this.#getIcon(f.properties));
        l.setZIndexOffset(100);
        /** @type {(event: L.LeafletMouseEvent) => void} */
        const onClick = (_e) => {
          _this.#_onclick(_e, { ...onClickOpts, properties: f.properties });
        };
        VehicleLayer.onClickArry.forEach((fn) => l.off("click", fn));
        VehicleLayer.onClickArry.push(onClick);
        l.on("click", onClick);
      },
    });

    realtime.on("update", function (_e) {
      _this.#fillDefaultSidebar(
        Object.values(_e.features).map((e) => e.properties)
      );
      Object.keys(_e.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = this.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty} */
          const feature = _e.update[id];
          const wasOpen = layer.getPopup()?.isOpen() || false;
          const properties = feature.properties;
          layer.id = feature.id;
          layer.feature.properties.searchName = `${properties.trip_short_name} @ ${properties.route?.route_name}`;
          layer.unbindPopup();
          /** @type {(event: L.LeafletMouseEvent) => void } */
          const onClick = () =>
            _this.#_onclick(_e, { ...onClickOpts, properties: properties });
          if (wasOpen) layer.closePopup();
          layer.bindPopup(_this.#getPopupHTML(properties), options.textboxSize);
          layer.setIcon(_this.#getIcon(properties));
          if (wasOpen) {
            _this.options.map.setView(
              layer.getLatLng(),
              _this.options.map.getZoom(),
              { animate: true }
            );
            layer.openPopup();
            setTimeout(onClick, 200);
          }
          VehicleLayer.onClickArry.forEach((fn) => layer.off("click", fn));
          VehicleLayer.onClickArry.push(onClick);
          layer.on("click", onClick);
        }.bind(this)
      );
    });
    return realtime;
  }
  /**
   *
   * @param {VehicleProperty} properties
   * @returns
   */
  #getHeaderHTML(properties) {
    return /* HTML */ `<div>
      <div>
        <a
          href="${properties.route?.route_url}"
          target="_blank"
          style="color:#${properties.route_color};line-height: 1.35;"
          class="popup_header"
        >
          ${properties.trip_short_name}
        </a>
      </div>
      <div>${this.#customHeadsign(properties)}</div>
      <div style="color: var(--lighter-dark-background)">
        ${properties.trip_note || ""}
      </div>
      <hr />
    </div>`;
  }

  /**
   * generates vehicle description
   * @param {VehicleProperty} properties
   */
  #customHeadsign(properties) {
    const direction_map = { 0: "Outbound", 1: "Inbound" };
    const description = `${
      direction_map[parseInt(properties.direction_id)] || "unknown"
    } to ${properties.headsign || "unknown"}`;

    const customDescription = {
      515: "Hub to Heart",
      520: "Heart to Hub",
      621: `${description} 🦊`,
      926: `${description} 🦊`,
      666: `${description} 😈`,
      888: `${description} 🚂`,
      67: `${description} 💀`,
      69: `${description} 😒`,
    };
    return customDescription[properties.trip_short_name] || description;
  }

  // static #direction_map = {
  //   0: "Outbound",
  //   1: "Inbound",
  // };

  // static #worcester_map = {
  //   515: "Hub to Heart",
  //   520: "Heart to Hub",
  // };

  /**
   * @param {VehicleProperty} properties
   */
  #getStatusHTML(properties) {
    const dominant =
      properties.next_stop?.arrival_time ||
      properties.next_stop?.departure_time;
    const _status = almostTitleCase(properties.current_status);
    const tmstmp =
      properties.current_status !== "STOPPED_AT" && dominant
        ? formatTimestamp(dominant, "%I:%M %P")
        : "";

    const stopHTML = `<a style="cursor: pointer;" onclick="LayerFinder.fromGlobals().clickStop('${
      properties.stop_id
    }')">${
      properties.stop_time
        ? properties.stop_time.stop_name
        : properties?.next_stop?.stop_name
    }</a>`;

    // for scheduled stops
    if (properties.stop_time) {
      if (tmstmp) return `<div>${_status} ${stopHTML} - ${tmstmp}</div>`;
      return `<div>${_status} ${stopHTML}</div>`;
    }

    if (!properties.next_stop) return "";
    // for added stops
    if (tmstmp) return `<div>${_status} ${stopHTML} - ${tmstmp}</div>`;
    return /* HTML */ `<div>${_status} ${stopHTML}</div>`;
  }
  /**
   *
   * @param {VehicleProperty} properties
   * @returns
   */
  #getDelayHTML(properties) {
    if (!properties?.stop_time) return "";
    if ([null, undefined].includes(properties?.next_stop?.delay)) return "";
    const delay = Math.round(properties.next_stop.delay / 60);
    if (delay < 2 && delay >= 0) return "<i>on time</i>";
    const dClassName = getDelayClassName(properties.next_stop.delay);
    const _abs = Math.abs(delay);
    return /* HTML */ ` <i class="${dClassName}">
      ${_abs} minute${(_abs > 1 && "s") || ""}
      ${dClassName === "on-time" ? "early" : "late"}</i
    >`;
  }

  /**
   * @param {VehicleProperty} properties
   */
  #getOccupancyHTML(properties) {
    if ([null, undefined].includes(properties.occupancy_status)) return "";
    // if (delay)

    return /* HTML */ `<div>
      <span
        class="${properties.occupancy_percentage >= 80
          ? "severe-delay"
          : properties.occupancy_percentage >= 60
          ? "moderate-delay"
          : properties.occupancy_percentage >= 40
          ? "slight-delay"
          : ""}"
      >
        ${properties.occupancy_percentage}% occupancy
      </span>
    </div>`;
  }
  /**
   * bike icon html
   * @param {VehicleProperty} properties
   */
  #getBikeHTML(properties) {
    if (!properties.bikes_allowed) return "";
    return /* HTML */ `<span class="fa tooltip" data-tooltip="Bikes Allowed"
      >${BaseRealtimeLayer.iconSpacing("bike")}</span
    >`;
  }
  /**
   * speed text
   * @param {VehicleProperty} properties
   */
  #getSpeedText(properties) {
    if (properties.speed_mph === undefined || properties.speed_mph === null) {
      return "unknown mph";
    }
    return `${Math.round(properties.speed_mph)} mph`;
  }
  /**
   *
   * @param {VehicleProperty} properties
   */
  #getFooterHTML(properties) {
    return /* HTML */ ` <div class="popup_footer">
      <div>
        ${properties.label || properties.vehicle_id} @
        ${properties?.route?.route_name || "unknown"}
        ${properties.next_stop?.platform_code
          ? `track ${properties.next_stop.platform_code}`
          : ""}
      </div>
      <div>
        ${formatTimestamp(properties.timestamp, "%I:%M %P")}
        <i data-update-timestamp=${properties.timestamp}></i>
      </div>
    </div>`;
  }

  /**
   * returns the vehicle popup html
   * @param {VehicleProperty} properties
   * @returns {HTMLDivElement} vehicle text
   */
  #getPopupHTML(properties) {
    const vehicleText = document.createElement("div");
    vehicleText.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)}
      <div style="margin-bottom: 3px;">
        ${this.#getBikeHTML(properties)}
        ${super.moreInfoButton(properties.vehicle_id)}
      </div>
      ${this.#getStatusHTML(properties)}
      <div>${this.#getDelayHTML(properties)}</div>
      ${this.#getOccupancyHTML(properties)}
      <div>${this.#getSpeedText(properties)}</div>
      ${this.#getFooterHTML(properties)}
    </div>`;

    return vehicleText;
  }

  /**
   * fills the vehicle-specific sidebar
   *
   * @param {VehicleProperty} properties
   */
  async #fillSidebar(properties) {
    const container = BaseRealtimeLayer.toggleSidebarDisplay(
      BaseRealtimeLayer.sideBarOtherId
    );
    const sidebar = document.getElementById("sidebar");
    const timestamp = Math.round(new Date().valueOf() / 1000);
    if (!container || !sidebar) return;
    super.moreInfoButton(properties.vehicle_id, { loading: true });
    sidebar.style.display = "flex";
    container.innerHTML = /* HTML */ `<div class="centered-parent">
      <div class="loader-large"></div>
    </div>`;
    /** @type {PredictionProperty[]} */
    const predictions = await fetchCache(
      `/api/prediction?trip_id=${
        properties.trip_id
      }&include=stop_time&_=${Math.floor(timestamp / 5)}&cache=1`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
    );
    /** @type {AlertProperty[]} */
    const alerts = await fetchCache(
      `/api/alert?trip_id=${properties.trip_id}&_=${Math.floor(
        timestamp / 60
      )}&cache=40`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
    );
    if (
      !properties.next_stop ||
      !Object.keys(properties.next_stop).length ||
      properties.next_stop?.delay === null
    ) {
      console.warn("no next stop found for vehicle", properties);
      properties.next_stop = predictions?.[0] || {};
    }
    super.moreInfoButton(properties.vehicle_id, {
      alert: Boolean(alerts.length),
    });
    /**@type {StopTimeAttrObj[]} */
    const specialStopTimes = [];

    sidebar.style.display = "initial";
    container.innerHTML = /*HTML*/ `<div>
        ${this.#getHeaderHTML(properties)}
        ${super.getAlertsHTML(alerts)}
        ${this.#getBikeHTML(properties)}
        ${this.#getStatusHTML(properties)}
        <div>${this.#getDelayHTML(properties)}</div>
        <div>${this.#getSpeedText(properties)}</div>
        ${this.#getOccupancyHTML(properties)}
        <div class="my-5">
          <table class='data-table'>
          <thead>
            ${super.tableHeaderHTML(properties.route, { onclick: false })}
            <tr><th>Stop</th><th>Estimate</th></tr>
          </thead>
          <tbody>
          ${predictions
            ?.sort(
              (a, b) =>
                (a.departure_time || a.arrival_time) -
                (b.departure_time || b.arrival_time)
            )
            ?.filter(
              (p) =>
                p.stop_sequence > properties?.next_stop?.stop_sequence ||
                Infinity
            )
            ?.map((p) => {
              const realDeparture = p.departure_time || p.arrival_time;
              if (!realDeparture || realDeparture < Date().valueOf()) return "";
              const delayText = getDelayText(p.delay);

              const stAttrs = specialStopTimeAttrs(p.stop_time);
              /** @type {StopTimeAttrObj} we don't really *need* to do this, but it makes the implementation of the html key wicked easy */
              const trackIcon = {
                cssClass: "",
                htmlLogo: BaseRealtimeLayer.trackIconHTML(
                  {
                    stop_id: p.stop_id,
                    direction_id: p.direction_id,
                    route_type: properties?.route?.route_type,
                  },
                  { starOnly: true }
                ),
                tooltip: "",
              };

              //
              [stAttrs, trackIcon]
                .filter((attr) => Object.values(attr).filter(Boolean).length)
                .forEach((attr) => specialStopTimes.push(attr));

              const _onclick = !this.options.isMobile
                ? `LayerFinder.fromGlobals().clickStop('${p.stop_id}')`
                : "";

              return /* HTML */ `<tr>
                <td class="">
                  <a
                    class="${stAttrs.cssClass} ${(stAttrs.tooltip &&
                      "tooltip") ||
                    ""}"
                    onclick="${_onclick}"
                    data-tooltip="${stAttrs.tooltip}"
                    >${p.stop_name} ${stAttrs.htmlLogo}</a
                  >
                  ${trackIcon.htmlLogo}
                </td>
                <td>
                  ${formatTimestamp(realDeparture, "%I:%M %P")}
                  <i class="${getDelayClassName(p.delay)}">${delayText}</i>
                </td>
              </tr> `;
            })
            .join("")}
            </tbody>
          </table>
        </div>
      ${BaseRealtimeLayer.specialStopKeyHTML(specialStopTimes)}
      ${this.#getFooterHTML(properties)}
    </div>
    `;
  }

  /**
   * fills the default sidebar, the one on load
   * @param {VehicleProperty[]} properties
   */
  #fillDefaultSidebar(properties) {
    const container = document.getElementById(BaseRealtimeLayer.sideBarMainId);
    if (!container) return;
    // const findBox = "<div id='findBox'></div>";

    if (!properties.length) {
      container.innerHTML = /* HTML */ ` <p>No vehicles found</p> `;
      return;
    }

    const lastTMSP = properties.reduce((a, b) => {
      return a.timestamp > b.timestamp ? a : b;
    }).timestamp;

    /** @type {DelayObject}*/
    const delays = properties
      .map((a) => a.next_stop?.delay)
      .reduce((acc, curr) => {
        const dclass = getDelayClassName(curr);
        if (!acc[dclass]) acc[dclass] = 0;
        acc[dclass]++;
        return acc;
      }, {});

    const delayDesc = {
      "on-time": "On time / unscheduled",
      "slight-delay": "> 1 minute late",
      "moderate-delay": "> 5 minutes late",
      "severe-delay": "> 15 minutes late",
    };
    container.innerHTML = /* HTML */ `
      <div>
        <div class="train-status-bar">
          ${Object.entries(delayDesc)
            .map(([key, desc]) => {
              // const desc = delayDesc[key] || "Unknown";
              const value = delays[key] || 0;
              return `<div
                style="width: ${Math.round(
                  (value / properties.length) * 100
                )}%;"
                class="item tooltip ${key}-bg"
                data-tooltip="(${value}) ${desc}"
              >

              </div>`;
            })
            .join("")}
        </div>
          <table class="sortable data-table">
            <thead>
              <tr>
                <th>Route</th>
                <th>Trip</th>
                <th>Next Stop</th>
              </tr>
            </thead>
            <tbody class="directional">
              ${properties
                .sort(
                  (a, b) =>
                    (a.route_id > b.route_id
                      ? 1
                      : b.route_id > a.route_id
                      ? -1
                      : 0) ||
                    (a.trip_short_name > b.trip_short_name
                      ? 1
                      : b.trip_short_name > a.trip_short_name
                      ? -1
                      : 0)
                )
                .map((prop) => {
                  const lStyle = `style="color:#${prop.route.route_color};font-weight:600;"`;
                  return /* HTML */ `<tr
                    data-direction-${parseInt(prop.direction_id)}=""
                  >
                    <td>
                      <a
                        ${lStyle}
                        onclick="LayerFinder.fromGlobals().clickRoute('${prop.route_id}')"
                        >${prop.route.route_name}</a
                      >
                    </td>
                    <td>
                      <a
                        ${lStyle}
                        onclick="LayerFinder.fromGlobals().clickVehicle('${prop.vehicle_id}')"
                        >${prop.trip_short_name}
                      </a>
                    </td>
                    <td>
                      <a
                        onclick="LayerFinder.fromGlobals().clickStop('${prop.stop_id}')"
                      >
                        ${prop.next_stop?.stop_name ||
                        prop.stop_time?.stop_name}</a
                      >
                      <i class="${getDelayClassName(prop.next_stop?.delay)}"
                        >${getDelayText(prop.next_stop?.delay, false)}</i
                      >
                    </td>
                  </tr>`;
                })
                .join("")}
            </tbody>
          </table>
          <div class="popup_footer mt-5">
            Last vehicle update @ ${formatTimestamp(lastTMSP, "%I:%M %P")}
            <i data-update-timestamp=${lastTMSP}></i>
          </div>
        </div>
      </div>
    `;

    for (const el of document.getElementsByClassName("sortable")) {
      sorttable.makeSortable(el);
    }

    return container;
  }

  /**
   * to be called `onclick`
   *
   * supercedes public super method
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {RealtimeLayerOnClickOptions<VehicleProperty>} options
   */
  async #_onclick(event, options = {}) {
    super._onclick(event, options);
    /**@type {this} */
    const _this = options._this || this;
    await _this.#fillSidebar(options.properties);
    super._afterClick(event, options);
  }
}
