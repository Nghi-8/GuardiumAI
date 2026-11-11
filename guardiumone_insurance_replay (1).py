"""GuardiumOne | Insurance DE2 evidence replay.

Run: streamlit run guardiumone_insurance_replay.py

Single-file client demo. The bundled snapshot contains the original 256
DE2 Tier 1 signals and the proposed baseline topology, compressed without
altering the JSON records. If BOTH JSON files are placed alongside this
script, the app reads those instead (so the same view can use new batches).

This is a historical replay of SYNTHETIC detection signals, not live telemetry,
proof of unauthorized activity, or a containment simulator.
"""

import base64
from collections import Counter
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import zlib

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="GuardiumOne | Executive Risk Console",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background: #07090e; color: #f1f1ef; }
[data-testid="stSidebar"] { background: #10141c; }
div[data-testid="stMetric"] {
    background: #10141c; border: 1px solid #303139;
    padding: 14px; border-radius: 9px; min-height: 119px;
}
div[data-testid="stMetricValue"] {
    color: #edcd8c; font-family: monospace;
    font-size: clamp(.92rem, 1.65vw, 1.5rem); line-height: 1.25;
}
div[data-testid="stMetricValue"] * {
    white-space: normal !important; overflow-wrap: anywhere;
}
.stButton>button { border: 1px solid #ff951f; background: #151a23; color: #ffb45c; }
.gd-pill { padding: 5px 11px; display: inline-block; border-radius: 5px;
    background: #342718; color: #f7b451; font-weight: 700; font-size: .84rem; }
.gd-meta { color: #a7acb7; font-size: .83rem; }
</style>
""", unsafe_allow_html=True)

# Exact original JSON payloads, compressed to keep this a ONE-FILE demo.
# Use the optional external JSON files to replay a new handoff instead.
_EMBEDDED_SIGNALS = "c-rl~U5{l)avl0#_<EH>enezO%$r~hbPdSTg9h+}We^b=ku!ujY=Ug+VsPRA?#Lp?o~ljvIoqbXHV1n?n(R6sb-HuainTH$SNxa%{|o;&|K{VDU)dMG`C>Yly3AxOmT)2_S|W)`tz%3qrS>oW=BHPD{OXS$uc^8Alqt3HyPSXX^1r{$HOGJcpO@dn^MC)HeEWwVzr$DGeE-9D^3C)#zm~85_<eeLES@9Ze*4{re{=it$0z@rfA{@YAHIoK{P}_O@x!+tzW(t0Kc#;w$-JZ~-+cJyt0`Z{tH1y1_ut6ZUw-`4xBDag({KOtm%sh{fB5bGsP=pR^1u0?;;aAVU%!yw#|QuOcOI(=&wu^mZ~pa*|L}MJ_>cec<$wC;zyIw&zWn}=AI!i0jePU*58r+G_N)1uc*PIq>H81geB&Pz{_7Y2b$`zfKYTa+%Xr7HKK|*)Ki$u~e?0L!|5`rAALjc%eD&?0KjL3}$9Tp^`R@1r@zq;B_z3Z$5Bj}-xBtfGhabNA_{DF&`QhuY<E_4v_)srz(LlxkGpFIuigB?uhkF@Vz<S+(hHvGYAD>)2H<{Fj`UL3ti~s&Nub@F}d6h+}U>gZlAyK26NaE|X<^mkgKm+r;LgPRE-S7Ux|NGm&KZ%Ur{qsNn2#k*(K79R~pPse<{rmLC`R#9(f1H2#^5x6F7&P{`{CQ+N{0zT1HaJUlG^n!()Lh<TLmjjAX{m8u37txkshno3-MKou;xpLj{jU!j@rk}#fBG^$!&mc9u^jRHc)xdp$<KeBUmP)py_l`6*$`mDflY>Y=(5tv3{hy55>=RqCc^M0PF0>k47Fc9V!o9>{V|^X<MRCU8NQ4!e)!?z=R(ORKEf}KjM^KFVGG3=sL5Mo1dYVQw$f-!3E6wnqAdmcj7G|i>k*f<TY_9gg0M)gHd<*=U=7o5c??JQP#MPl3L3MDhK}HpSwQpvjWHF~3#G~>%1o7!M2M1S$xyhc6nF+2w*<L_1UZF`f?CU5OII;i{eTV6wa~DUa&b)vr6;neDyul46l*l-8Eo7V<iZl<6k=q8hLFH%IDoajMGObe6y540dlZ_P12JW2V$5@3)x~o?gP2=_TtI@HLdL)-FvaQ!&${)>TV%AUHUuppt^G@-q^;HXC5QK=lB?$j$mq8OxrziKmNuG?29p75sLnNX0Bx;dr1aY9l7>8;rQ#B3IF8V$(t1=F74d{!H#DH63WK1N$D2O|ja!0TLV}#bMpv9m8aG)$72je5vlI>6o5rjmPhncvS=9tw9g25ntj}QMmLM0FAg2&hLwrDPMz|(Sx1-lpuJONwp=<XpNKFDu5|q&@yLElIZ`N-KauEq~3K?TeqgqRj>H*&LEi&>FCYd9_ln|#Yeqn2#I@h_hQ3w-#fDFDR$W<hW)Y`&NXb))txLmsA9y-#DAlz(wU1ofWX3Ug9!2KXWtZ}VVA!z{&2~v3PnzrPHamd0MzUCQd+!Evx666#%a`9T?39-%<viJcTwaHM=sSXO-$Q_ebwzQ^0RFoS3tj}QMmLM0FAg2&x1t*O*i?Rg-=&%c7T32h9Jny5s>YkWZPoZ^rWDFOa=QD`8CCCLN$SGuC&BM()cb^ald5a9;tkP(tJnIYzG9;|7Ve-{0sFm7{KaGr1ZwYc02~roYnisby4|`)n>*%f3IUVc7HydOg_?gfN=iWW@Lz$uQxzH$<+PfyiSO5lVX;cHnQ8KRb3^Z;DatR4?3L7g=?h4vx&M=Rgr?grI1PN@EFt%ZVleCpnTRpstPH8@$!Nx5?E-XP#A%<;e%WbtH8R|G3-36kGk&k3uOTre`CL9hY4hP&!6v>}rlUssZK!Th?M%Y^s<-v>uP>#DGVR7nME3Gj%mvBx2iIH^08}_2m#v^3lEkUj#LA=aNb76CHsHN%1&E{HA+ORcVtJCFqO~gROf}d+gouPE0h$J4dco=V&I2TN1AV!6%?7+`J<CY+okRYe9k<q=EI$E0zjQA}!0Buyynu3Y)?ggny^Q1sYSl##*nafkyxFyJiCCDkngdqmcl^6CfDtc&OhRh;Mdh*b<;dKF%P#p;%$YjQM!6nZi=9VBAkRYd!0WB;E7k8W$4EkY5b)fjPC@gJ-)h(n+HMA;P3CSAVqU}M?VWC@sT&5SqDi*QcNd^cmnv@N!VYUek-jtcWW4=LD7z0NKb&9Cd3`gqALY)rVq#=;hri5-a>W<Gq<CY-T=mj~0jc%5`<dJ8eAbjiv8J#NaQ#l`;P*IW=p%gMi2t}>8`V2O133BCLkTZxG3#tz8tF8<K5Bp}BR-1bl#AWP4qbunQL*rfeMYjy0XApBskSp|poI!>a4Wm1xcR)}%G%D}oIkh&^)~_K>Gbf%M67k>#K3i=M>P#)S1i4HvNI;<*&XpU0l+M&cfiBTT6Z*^b>c7|psUyq?3&8FZ>IZ0an$_y=G3>riZ?&hroff`j*(@-DvpxfjTY_Ap7vu~!dPTPx#wD+K_BeQ2)J!xyupz_3uk3x(vTsXOTT-)AMR^7rw*<LzFUT3h#N)&@%nSr#h>ka6Ojdzj0xY>F1TKjr3Qfr#MQfC$3!XvDEkUl(3vvb-GXu5lV|pMXmv#`Rl_qaHQ){KLx+IB^JrpV!cN`4-sLsGGL9QY}EMu#-?`k&%Z!12{zN@`#06W_ob*iNlZd~dTu-cAWr)w3ok!A^riZdh#ah8y%qjnFPnYBCvja!0TLV}#aMi=1aOKfR@F%H;ZRD|k1P29&Xy=jtWIZ^0VT1!K~_%qnJCCG&($SK5l$%UMpDNGI5WA{*{F>+KE%2PsuG)o$CB7v!DA6n<MXApBskPAqVQ^;65E2z2Z$^wpu9aSCfo!Qb{7ItPCC4Jd^A2k<_ZzA<U{!|^e1i6X?$rNzF_;IFY5VBM&X2`gP;mST=w+ZPS$YoktyBVY&!h~|upp+&lwChN_XFYsNm>2IMOtp<nk6I3YgvKpFE+IiqVZ)bI3{wKZC*bqYC*+HBpr9pa0~0E7;uS)bJjAJXQkeb>Hf{-WVF_{yF-E;me7)z{pwz?tx;#qGPBU>CEeuVFRxN^wZCbNNwlDHNftXu@TtI@Ht22mAdTw6A>MlOsh#B#2+&oq1l@O_f%WXBd#DvU{9Ue%KcBi9WMuNc5Le_kBt<b2kik2eWXDc#CetnaldX$m2_rNMlIQSM78rd<YfiomXXGl_dPGu3!>Z|&|XP|LQkV{CAQ`jKsWi{_%OdO`c@gm)7EILxSl<>5;FKlCok;=s@h7YC;&tT)0AQzS(rw}u>w%i*mREQTIBnZsOd5x8Nr9h1GOUh7))+V&J*aghbAm)}J7my&QkTF7<tW^fYx`D#sx;D<flsfJE*?HF)OqBPkPb!VF1~?wrnRch6UMC&3vvfD+p&jzd$~8}yPRRLXcl4ES>4H3#WS0tthx7h2GvW+?E280aOApJ!5E5jTRr{>DAUy+(TY_989rX-0)|%XUJhkoz%K;l5EQlk=-+keY4YQpd1F2YDqri0c{tPy533BCh)H8@F)C$%)Wy}gv*5TfRqBY>0c176{sggpe?vgXBgx~G!QPy(1(@`&zj(P?ez6b_qZ7Kkhj-hqAhtbJ(w<m9Ly7$MZTN=;=<6E}wk0i*Qj(QylQpHGOdAxLJ)@e$J3)valrA(Wz&-*88=F)fq?aqz^Y2?w+cqYxZBb5<SyqhP_KnuLtnEVVhZV7S?333J-s4qSz9E~8@I_`pmrQMl!X^z(SUH*N>Use(ulx6ii6rRDxEkUj<LCzp1)8uI|TaTr;b~y2$lLtpdNz1A4LKC8u1=FZpm0AcB&Cej_mLOM<AZL(KfLC4nM5QiR<&YQ?g{2x)Oa*tB(DHo-(^~Qx=7;7^HG9yG+U|7J%Se!6i*m0Oh7xG)($t!>Os%o@v%Ge?;ah8#imMM;`H=k}C6^hXNtQ7r2<4TiJ0(#l8&l-Ao`J?KK`tRdPGN&umw}LH=m}{3;9QCo*l)P8Q4=<@#O|C-xmTQ{<cGT;cRK3TCCE9%;HnjQ$(Wl~;26*jCD&O~@lHRcKQK(#5vlRd()t|m3}S8xasdf)3K@ulYc}=T6(}FXDF>6dDksO9!|F;-8d5g-QsV|x8a}x80Czg-btdIv;T?jDc^{cfWug_!j)S_1$?G<ukP|bjphX4QW9JT}Q6PTYeWay(d{A$mbm!=5i$A8Jtx@S2XxtLy8k2HQVPnTGQy$(BLH)2pHU=}9Q7YQ^jF=h)CAYA+AwPrzHT)<S1nzXy%TLNZgBWfz7QfZH5rfA`APq+L5;j-XC<&2UVx63twCpCO)iRzz%q>B#Fe&#8GFsIloy4gv=;hE0(z+7PE@^RzIy2`=;ygpEHZOv+SbZQ);Z8@r&ZS%@3RU5A)O{e2+9mYm>?Iaf2jiPDb)|{~U&sW=$4R-+ws6Ikrh7{`RHDr6*_KUeuUs;5eg+!11i8kg+%wpK7P53?SZfFf9b@apq<vX8jU0XjcTTEu>1j@nT2ki>Tl5SzZV7VbOSxwdlWpzE9z7s~03gRC8J>Zek~}-6Jv=p0S(+#cR~X-Yf;XQ*%q>B#a4Gi;G9>CmTRePr4Xb+`hgvbLZOLiJDkp4^_tfp4#?<CRx`;lqGj}@bWhBUK1G@p$-a5>HL)XkuSDkClY;StliOX7xHiUrnFe9e!fc|~m(gPzqnrz>Hu$^DWx;^roj|Q^CosN1P333V>ds97V0HbC^Jt>E6b+h?md=kr^5hGkv*qo7uzKB!PeX#cgHf{-WVF_{yF|Ik6teaBeCC5D75q`#MAb<>JASMhiTU`kX^3FN5s5j3b=9VBAkRYd!VTH=<jmwDVWI6=2PZ>C@&(z{A6Lz2Ba)Vl04LzH&8m|Y)z#r35;ljxH@ZJ1Fs@lDjzre-c{ljnn>31)`|M6Krd}IFI|M%TjAHVwM_X(^7$v!~DU%c-p@$mAUejX72+i(5U^=!xLf+pS^1PbjmDVWw8PNdGS??!RUO_%2>4s9J2M<8f`_Z^u$LX7f=`l37avK8_=i(BWXkkGFzMt^pZ|F@F#!?*s8eD#~(fBP}PhX-Kz`8E8%5TmcY`7aKK>@&n?&!x!(o`)L@3z6etPova*g8_Sr_l5m$B+xNf1)qTf;Dw3d(`a}jHNJEE>SNL$zH|BEg}T3u1^DvEFMs)+fBWIPkH0WP9;uBdKG82vBQ_9AJfY&g3~>yaDiZ@xHH{D@2?3*^46P~WX`s4O?Bp5TaQ)R6lsAIp^OTaeD&?15{T3gvHfj|bzKoB1oBp!93vq|7$5YZyZcplSCWEn?j&o(tPpv-QI~o^=89M`w?ko3E0vxbl{me{{J@|MwOfB==7i{<NxiXSt!#3)gJnS(v%HKl0cQmdLGj;|WOWPD0wLx{L<8T&R+Z@`<K8ux>P@Ph|AEi2S(a@dj_Mjsj;dUYK<U)MVKmep-0?>>}m5NSX45IwzZbDzq%}Ol<(2w_=V9){{JyGb3AN{Bd)}%wYb1h>sJ%xnZg}jpsIRyvLxy1i#C`y5N-O+_`wz4R}z?VT#nk33hsL3Wm6G(e~1`f9ixx5QGg`3^*S6eT`gGP8AqO*%n5FaZ64oZkRlJpgXB3-f;u#xQ<+}tkYGr5pctKZd%^KfTXa5|p2msS>=C0jdAF3)|7scKq)R=U~V=6Y)NZx?cf!PjS?!D#z363j3Z(EITugr;&(L2|MkcC45P3Wh=51IAWICw>f#+l5?Z@bwvND0-dP$Ih;W;>TzX?$ukMQ#8l|+jgjHcW1;q3c9v3A6!boal4Rrav@T95%n>50L!E*yzc}AKD-sP{<=3fe8uXyRVcH8>tXXdoC!^@BmC&{gdWaRIY<LQWP$Cwj`$Q3ZWr=SF60y(*4ll0tx?ATc^r<$R(K94;$*mIS2N>o1s-YI%nnvzvOfcd+l5@-g`C1oE4|lE_H`JncDSxIgA7-%C2C3O`~IsXX`wjc`K6Q!$o(nY+%DuZxsY?L(Wd6b-e&EgK#px%1AVofSzJ6kXs|?z8nTj#^ht|3!+dJ>Zx?cf!Lw(eQF~#^Su4*Br5}#TNPwGjOS!GQ&q8wI5-wHy5DT)vMfMmPw+p$-;Mp_S$gpyox$)=>%MRKTk!bDf0>k<~3$dB@<fkOKxb`kN+b4Ix_xb7VLf*-REYf`jDqWd?K)6z-l3kIT0m7TT3JLeY9VmB@Jda4=3AtLr5o8sdkdr{86kn~ytM&Zp*^vJe3AYP*Cl_)G4lOic*H(NC204b8%V?ErSWy$+9a)9;twc;#v@{&GWrSzoaJ!JpyO2}3u~=kKDHA9xMLtfsSF+rU(wal}2?!*GCR>prO_@=L)-$-dUC3v0A*WVfJQJ+p1`2_K<7l0cGho+P{k^Fv1(GajVMN2cW@FJ$yO966`nL<YfD1VVjj`NONGd|;45#C^RxVujx!B?m873<+?2N9~YYk!`#`+i<w+p$53puMjy;#$z2~j-CL3>v4ZmcVXJ{<{R&cr%eQd?NUp9ZHq(w^;hA@Afuh>Fqb(gpVUcqW%(gB{Tb^V=|tzRFHfQLhsgl;ebYl!3uh8N!rev6Zy8pbDWtNVC-zJ%xnZg}jpsIR%Hcb8l$*R2g7=&=c`RLQ+n%w$Kya0}gxGxO>n=C1D#+!Qplxmv<qjaD!!pkx<h45+i-MXxRHK#(AaS7~c0nY7#1S4>t%F>180vGq|~3$Y*jPr&fRFT1yT|LDQihlP;K=vh}{xwSqMWdXlPj<A5O^@Co?T>fbKp0xskfG$?lrnTg!PsB$~F5N~7fLQcT}0f-)p9=cOf4cjsXP#MJ^L*sTK7jYry#74$YkJ`r076(3@g^X~ay^owk76w`Dk<mH4D*2wTwdZ;Icz}(5yO4KsA#+jVqJ*OnWb5%sAby@}_(#<y>vinf$kXS9$ss?B=R-sH2%nO}dyvOpHFh6~r<Jr!k!+cS-F*rPw+neE7jg~`drsaOP)apudN8G4t2Z1yRo`9xgne&aZA?hD1#4d~d<G7;3%R@tIfa`hVO(2SjXWl3JGS`FZW^^F<*^3<vufgkds~Y~E){0{`V4Mv7xI~0$f?ygA3V8Qap#}Qb<L{7E3K3Z)6UzgNms`-e9gIV4{qeAR{wS(SIFBtMGS*ji^1L?2a-dJuV<@S2$M^20xph%(qdImXDHaY+`K)8#_d9`lDBt?Hl)<>DGuxwmgU&3H}h1I8e$_u!a6DOzFjt4vQ!uzyz&4We7lf$av=j2j8+PE1n4G;fs2{B&<Ga+Z%#~c-xt+RU<P>X+my;-WAjSfCFH}J!4gb?gf^P5ymma^Q%Ja7$UC`^Q*fwrN%)K`!%KLI!>(rE7Y%2wY1Y!hh143r=#mO%>1<AY*)wpsUC8BK$SK@->&VmA+PUAxhbfDWs@X|Wr9EH3b}*;!Sn#MpG~3Gkxq@=Lkk8~oPOZLH7Xq)YKA{{Zz*{fsf}tcNN(bgule9jPlh0wpY1Z-7>fbKp3gcJLK*JEp<5{RJ9;$~{O#mHr?IU&D!3FX%_N)X?bOz7dp$a~R#_d9`GJf@x*nlAo!cgo-#yVzX(NHXGNpaSMfs-UN=fqWY2X8II2j^s^-Y(>wTu7yb!R`&C>O%w71*>%pzY)H{puO(M@?Lx2vt%U5A|DEf^mvr^<`uWGJF-d=wUGj1OObM>N1NY2A>no*@8m*G!2!Zy<ahv0E6_M(9TCgy(|1I{4sI@OCSH(}j9Rk|jfd7VaJXH_<z2`r+$i|IXBdx$t!V8Kg;RMFSLn&Kt#GeFBjH&+XhhMdz^0*RaC5tm&*VZ*tv=aq1}_kzA%Fmfemp2mWro09GQx`R?#RlerM68=74fY0)au_Z<N_|_6f|s_X%_86cc9H7xL`u2JSqO#_lywq5t_62me!6t7$9BB6H4=TAs2BWr?64`n8n0elbwlk*t%kChy^+2vBgF&z9UUSfackV29rD#8+f~r_e$!Gf}pH8h89@0av0MoJ;0%J_O}-ct<MkwuG#i+$T;SCPlE!M+R80qZ7qeIm}w2O!n+@f{V62eF66zEde6Xtk=B@=7dG7SsRv@<R)L$Q5S%@s72V^>MyiG@hhybsPr>1KA=gjpJ%gKu4LGkVyegm_E*f&zGV-D%`&<>hO5(QmfcBg_goBN0^9*io7xKB1dQTM*pj<efJMw_O4swD}sp_oB%z`x-F$q{rG`Wp6r5V(xR{wS(S4iqT1q}uyoiuBOpX>NG?NM_~Qif6zB8JioY$OgWl`OFI8Dh9y$W@Yh&tOCIsJa?bW`o6tEzcF+HSCO~y}uFKGnaq`TB4nlMY$Gv)W%!rb|LSTk%gIjRH%E9TrQ2u2q4fTXrocr*J){uDo?dO>Ht2nM4qGDFiJDrY9L`@qSkwoDLOJ(w`NZv;dUYKm63G@4%}-V+}dOXm~d$0Wi8o|R~ov<nXX_5#<F%=R<)p?><rJq;dUX{&&WE18zG5`(${i!*tx53Q<5z21CNpNS~c8j)DrGcUZ$^i2Ajp_Gq|~3$mhz)I<xvaAFp{hO$a&R>lk)3YUh&Y-mwTd0evP_Y^hVXcxhRlpJI*Mg<K*d>kKqHhe+_=xCb$Wd^omhQZ3CeG0lKR;hHpOPJQ^oLCq%eV`$ti<SH3ir?e+{rA}Gm9{{KahbkpxMk}d|`l3B&B8X+l-9h91*3<{ssQ2vj_i`b7gssbh-U`I42KQdtpyIXVc#k(jk6S#Kb<hq)nsRU<pc!P0mV}KH#&eQb&{hjwF=>XBc+}8c@7d|^>OxMzLAgm~Y72>BH9roqw8hR*C7M{ckbTP-afPTTp2@hbN4uK!o}K>da3QB~(<WlAReBAv!A!?&H6|y-r29@fQs4j9YwFO&SDA$#wfNS1cKYXZA*WV<brdS>*#?5>fi<MLnFUQWU3+9q+k`PRfy~;bFIIV~h}<sZ3NGXnG~5@++OxC`pu@3M6IU;~AX!yU_!7j5W$$w0S|LxTLVFC2+l5@jg`A@eu{k6Z2Zjp?-*W8M(@{z<DZ|=#%2s$)#t@*>TZc8Fz=J@}de2UOHy5(@;g?!`f<4-!YaPU>nbs<mM}9p!okn%+g~BETOB`;Gap=x08dek>qkv#Z3er+AN7rnO{-_0~-m}x+*M*#cLj}*Pw>HcgjC|<urdAEIj?{p+ngmM3g2`r;se59bKLv-|g<Ri-oWf1fV2W%?u7K;%{v8q(YQ?~T)J-E}C0YWh$qF;l^8(XnaC5tm&*ehStiBqNEM;M;AavNus#c|h=17Zo+YL#u#^90$Pi5+JvdyPf|8^l)a3N=)v3vA1exV(`yV{{yFFZ(_z3ot}zBVz`L_Mqs;09H^6!3|Ha=VbLxR6stBLf$Zg0qEHtp^vvb<Rqe({AeufH)+g9@to3gETBxd~heZ-m}x+ts@Jd*$|{$6buWmZd^AYmJ|_seS2&;*wlg=HrB@>WU&jW!nD)_SqUwB(o#nPb?;hwZmm9rgxiI@S4Y+vIMAL0Gkq<}4ScraJ=0nyh6`C%LQM)r(I`<vDm2O5Rdzqd6L7d)$n`t2&frD^1p~|$<^uhAJH5O(6q6)H+uqhHNd+;DzD!5x5E@V6=5`^Ut0U{o>US<)iEvZ^U^}>wfxH^5oI-PKy}4T}_FuG7?n|;X_os@;?Lscmk#$O6c*uvaArcUQTGlZmONQH$L|8&;me8EsYDvCF-PPqwpg)Gj?Lw~7k#$OJK(<ypK;<wBbnMm(WtvCssgSLorbI{{DP%?qDqybiz@fH#cKUm{5Q`P(j9Oh|g;mvCcj9oPGLb32bs=Famr@mm)(*GRYj_RCC>ur)ERn;MDpyU#hX)R@`l?SM;dUYK<U&rtVGPE}R%}P|HaJc#)V0Q1nhbq!PjpGT8!XzCc=xhKyyzJ?+%DwuF60z$)c4Rz41OpD)DE~=VKh_(LTB{Qp|e9G5ll@xSzRGTh@QdC?Lt123pus=WpV?ac@H22w}S`G-3B3r)GSoD)PyA2F!h3SP$wXLZuM^$asd}|ju?6o@@+wQfFE0Yt7RN>*0gBmgfL2yvMh;}A>DdFpC3cxb|DvWA*ZlW8x0&CLQfc!V;irNG1Xpoy$G@4c?E5Nrs)F~7nHFc+)i)z?DY3?Aq85s-muwp*kR2Kne)O9j7r&FUq@cVBe(1@6zXvsD--n2zPG&lJ_{jE0`c1n+_<{fc+`>A?%C<@>OxMzK`fRVYvoxL)DNa~xGpatAII!%2P^iZ)g;YoyFDuh<>)hTxLwHQUC24yK+7|ivXkF|^UoZq3ie`qw{y4nF0({ba;i1+-Ytbi{0wex7xI~0$f?zDjY3L<@<32n$Dvd49&>1o<t{s$V2v8A(KK<J-f;D-eLl7Nw+p#|3poW10D>{{o@nZ@ay{;MhZV&>VySmQ89T&zpNe$q(@aY4eLRN7?Lsc%LQY|$?^$%AArQ9w9LIdt-LA<XDdb2=SZ(LC#xLHhQV0|c)_H)9dv^MJxsZKDv|w&j;)hzb(ehQw&OKT%$9SDnfMwJnt<J@}q5BYT0<9T=QVLV*JKjXn9zc^;Cv`9p@A)Yt+%DvuT*xUn^r?k={HVJNz&vbSEze$><%F^$)A}A~ITr7`h0+QOkd<fPaJ!JpyO49ZSw2Ei?$Ndy1?M0(dOSFKcvhRRJNaCbc5O+$!+uLBGM~ZC?Lt123pus=Oz1_pHJ$>U53Loe76gHkR?T~AVJxbs%tS30u6xFSJS8V?7jgv`ataz`N|I&7vkme*5JS8UOX-kC&pQVxhd1qnX%-KbSQVPp$I!T4$VFVpxuPMp4WdvHg`n%<GU2i?r13{eFf3?87?MC+X=Kv8)=+(@J@47+@8v=?n+o%qYgSk|*|YZ5g>V=szs_t%-AM#(R0vbi*C8!!T1Hgm1Wh&JiYlU1R+?V0aT}JGK81wag}jpsIR%H^Hp9M*#~wy_3@fNMf=pUYYAcALZ+l9uCJ$9%V>uRl3J$jmxx5QGg_{y014(^B-3bM7oLVSek#m}3=Q=O&B-mG~wZRwy;a%Vv+}tkYGr5pcs}H%<uElMig>*W!R%qQ<Mp{Yn>XwjK-)%P(VDFMO{@ZmvwfeUUxqu5f1r3oX6m>fhm_Yf^tQQWnOx?q8Jvaf4`ktchDX66L9E5GiV`$ti<RUKQ6gJFsHaBWL4{*fe4)|QcrN&zC1N2%YQ8q|TCHtBPxji^1gC8emw@cH;_xrX>@fPp&@4*^>@%HaX8X+1>A!)jD-J!cgWQ_)!K#33c8W^LL<+OMhw-6MEvvrW_*0H5Am;)GGl4jSJyJf*OES%djzz9ORFlqceE?#p+e5<eKpZ?<K_3IBG{@V}Ve);3qzx@8AeEi}2UkV`)xZ|nM@{40dd>?;6%fuEBx1;i`Qik<Zi`t&EUK4rPmgz)3qBM<1SBd~{61fJ6Nc_0B(o0{vnn;m6i?XaaqvV*rPGGFnrmSp6-T{vh2i&8qxJz=y5>}QdiF8i1Y^wAU>Z3gajGII*Ng}7PQl^Jk(M~c4lzC|7^HyfDI#RE?u`+WK;ujYaj3jD`52o4y-6V1i63J6I{+dE|l7beK7iG$V?7cO4b72)=&7rt@Eg*hKYb;SpPyv${4<$0uf<%PUn2-TbI`#GpFm4jLB#E5DO2|$vTY{{fLGf@ak%<7fdTM#Bu(~q}4#zKRFu<r2COsH>hvg=bYmkUhUUgEdSO`XweSxf*NUQOW3a^2Yy<>c4YrS=t>p&un=dxgmlwCX_7T7mWM$)2nW+WzE&j8~lkxP=uDXbKZpYEBB#50WJ%$nNFcn~J5fe;*hrl6*l8Zs<vSaCkEGYB_{T!Tbn^;b2j&Z01SXY7#kE;WW-m%ULUdGySA&blMx*Uv;}v?w}ZXM93Jr<nw2th+5D_Q~Mu8DQKba!C?7g_SnOp0!<gV`0+q6xX47IGu#7Gwe)<q#Z|Ub!q4q$2uPLlH#~Y<QgQ>Wi>WY&y+!SYbP`vy^g3XVQJ@UC4$~^MfcSmIv<os=Utcf3GH?=*lUmo=bCsznCGSe5P1d|H;G)5L{4D^$LwPV1Oqb+KG>N8WZ_{vt*9&s+ZL>Cc;a5Dh%Z^6o}RaN;BOMS28q=DqfX&Q*Fq>hbVcdt!X*@k>3FlT8ii%@j_Rrv;_1hm3L1}PN%2m7_j*uL$+jmE)KI|2jPMLFZW6g9iJZfVh3~CiV73f=JmSSVy)e`?d}+v$I`&Ck4Xjw$A8g8_KEO)5N#q(NqL9}LeW5c7hG`{hGk)BMf=|aLZ+6^gvpwo&PJuy(sRdDYN*#G82fu8rGA4?5N!?rU%UtNwo&m;9B9|nQQ&=G`nHq5Jvw_*6y)4ktl?YRv`>K7-E$IwSf!X&Ec+azy2UzJhiClw3;seMiom*Q9bq)@U6fs>Dtc0p~-6ui=v`;|Q1?Gq9vUC<1b06^*-cxZ(5&%tZth`2p2iF+>42+vZE=eM%uu=tbo;+Tzyuk6MT-`%*_TcBXw^Pw2C&?XCJQsJkHRVt5p9NO<CXs89NO;?6nPCmc;2i&%Wj39N8cfjF>y6dAWN4jrYKLxzJ`p#sy_B#s;(JJAd%5zE(-_*q>QWGlJp+uJL@r4pr?9fTs7P09vO`=B)>o-oW$b%SN|4A}QE=kT6Uh{I&VZlJm#n`jcgN~gI#zkd*=Jka0WvbL)kuXk@9ptY-`sz(Y9q`HhN^&dIJTP@C5l3w?$OT)OVLD%o=RApZVM4jo&m;9BG>F#J%g2f$zc*N>|LRl9wUH8?+tbLnav=P))V#OJN*SFFIKk)1*hB{t5?|**=@@{yah2pX~yJ@cPHU&RN8tC3@fqDMryJ$EInjHErM{eXbJY;Jg$sMH0T6YIGfo+rdW9f7&nPrb5G<9R&)*+bLE$F+`0}}>6tnat>kkjP^$E#qL7NZ>kKcX^1#lNyJPhtB;vM~>f#bQ0anW_ot;V^g+jZ^Yhc9V=%q>@vC4kjScU4{2|T&_*qdb~X{#7G8F@jTxlMTn7&nPrl0;5nrH2O1XsxPGs36CP7*xyIl7Q5Nd1_*Wk&28pGUaZye;O<G?pVEwov~3luQE9kEF*GSv4FD&1eDtAd>9BW=xe!P&oJzeO^EJXqD&<O+@~`O6SZL}Pndf&Xs2e+0OKZ+YucGpSTXXExnc7bO61tF$_kdl@YYgk$6!-p3QxnhQ;=uHIv*&JdUvc|rB6ggHD%6L6dV_Em{=aFUSjp_ZLYp(Q<ge&iRyA3#xh2gz(BA@hn-AlNv(UTQI>`js_WB(>HiFjn?$bJCvpZW8F~(m$XIE@C<m<M(QC0XQebLD)d}e;JqHw8lpW85aL@y++#RczQ6jE;j9>9uqj<!R@AQ&oa%qk7i=zCCBi`^bIFMl$ham?$vq##m9gEv{7;eA^5^Kq+NglHIL`Jq}fN_(^MU}`2tgK$@ZZxai8mJ%V`qYpbQHoN}JVUhtB$*1SMu}<?UT9SOG*;T(v3iv~k=`4S&7E$%w>d&=bOVPzD7**o8;QD)<-AB;4N5!MnI*fqJyvZ{xLce;Np~K=)SW-FV<^^q1{gPqTysz43|7kWQD|nA8D_R0urlK%xs4jCHKZ%HIrr(VrX?iEm@VrAJJWt$9jo=<mqhA&=85dv-OZtC4j60_u<G7IpRNk*Z<11{ENT!%BpzvYxI43uWaMQD@|LKi^ka1yp?q`p(MB%M00a2fK_c~Ykx0Epp2!)jWFazV<CPoqdccY`w6+JlFp&PZ3C|_ZfI{JYDR^Lh(3sfzO(NGI5k%HZo&jB88IuCk+}0{eE92`f#GYq2rH~YBZ<QXWhLM=j!X(WD7@<}Y4IT+BODVZm===;YZW6g9iJZbpj)D`6lXu@T03D8ar!ZJ3n#98>q0W~Z-xN@wwL;Ezfc5|@e3QsENF<bK9<}%kEeW(-hfpKNFdj3+D!rK@w!?I#nKpzWM~NDKIqZw1x^tFMqq-2yngodFG^~L68DQKba!C?7g_Szi82bVqwooF+*a+IeG<(c-a8OuZ6Hl_GD{4`vH88%zr?K)Y%UJzuwln**zvE8d?OT#ct2TU@d2hY<*T9&2LI^<_Edwwe+TJnO2{u=fS^^Grwj?D=%uYnZu3QJ?XMk~&$TjWE8LXJwnjI$+G#KrGm66@0YfhuU-V+&=s0$|*Sq9#H@B{1nE6Z5@D<+W=b_3>IQfz^C)xHxnb0}BjAu?WXta2OddE{vgs2px)GA?X;&chDGODH>NW{)&=Sw*0A%!bbZ<0g?ylE^8n#9~WbK@&UgupF^ciUhSlOB}`~VW26o4otOsK^mc2*Q0_%H;G(>L~1V}Gmq}U3*l5$%>-OaR$i9<bz0T5cph<v#^7F#4MdaI@O_I4W>gofi7Sni$E4wvM=tXjVB92fNfJ4Q6{Su~=j2{Oh_*w=YP?sD(&AxwWoNAN3an(@*)u~4sjdDXPvlpYvHDj`BEBg6ZI9(+f{81B*u4l^5$;hF-UKzP%{nAcDPspy9VBX4<5kep!tHY_aN?z!#&pe0IQ)^F`6*-dCXp+W$SJIZ@flQe&uw4%Eyq0GKC)23L{=qX$d4o;UQ)0Wgkh@L@j=`BuPkHrub4#kpdc$_)IK^0z@810rJL4;6KZ*FX9UCKa`TY2p+xkkME2oK_hfz1?pSU6h}RQ@J{`@+5aMTmag)d;N#qn(kVCWZ(AvWLG(N^ggrC``z)@@Vq|6LGF}v)Yc+IV81$d-H#!VvEAd%L>xn>K2Ix?&pfGA9?8a1Z({?at~m#xe&OBrp<mmv^`P@-_M>@$1P)x+nOUbdaF6h)^p^|Im#&j8~lkxP=uDXgq8y}2tED+r|?f||JyR2?miyl?T2E=fb=rde_o0wRY`PQYuwwv5%k=F^$JuU@-p>kW8x&Y>5ud6^TS+w0A;vF5135@UuJw&P|Qsv~w>sg7DhiQq^odo<$E-5K3imhucRZW6iX>C73dR6~Q7*Y0nHrU$HaTe(xL%c$g0a4Mvo1D&YEpLq%CgXz2N*OsyR*KB7>27^7ykTMjhVoT@p7Pe%%&Gx#L*^1XZd+T1o`f&^Z4CC4%WtlAnrIe&BBaK;mIGsL5_Gf@`lgKsg%o(h><vBLhtWm<598_z(!g3j!`r1(d`(TEx%wUqvb2@iXcz~6=WA!2=0@FrqXw3V-MV*~j*@F_-8WrA*0U#P)sPh_9VDZn~oymDltVwADgTm*=D|%=WqAWor!1N3-ZW6g9iJZbpL&90KXTkx-$9Tk9#LPGabFAG{v=X;4HUewqIvdKT+uqx+Eo1esxnmU}TghDNSU~Z^pVw~ou&k4c=Jlr8tT2`#wf878c-V0t%D4*maJK|OBH?KyEN*Jn=a@P{xIY7on?$bJv3dq8C~XEu^r;pCwZdUfB(Jb7?8&3D><f67c<g2~ju(MS<N07uq}&~=7a@^J%uMdxx`P|&8aec8mr+a4>$ODHpokq45f35EcAT#o#l?NBRI&$&<UIy}W=X4;(X^=0glB+plgK4W<Q!Id*HLAeG>PJIILQNT9)hE%j*ffyyCvDlX4(dM(1})mV13Kov3eCH!o8?k0HZq8HkfR<4eQo$_BS^(rFG#7zMKK_I^>D)>IS8G;)-+MhZu?7Fm(xhWW`!ac?K9aiCj~OoWV*9=i{_wl%XKw5K1I%?Vo>1n`ROgY)SYf*-UoCz?v=(RBO3ARxe{`P{U-fiw%%zfeReOVOEsO(%1JPVu5F=u&N8e$cN1`m=iG6NJ4m-Y9=*l86%Oe-hzM#0G<KHO(GYyGbgYT4ri8Sxv}fdg%SnF%*LTw7cAV(W}Y<H9ke=gym!c)Pv7EgzqX9kzhV-JzoM}tcfD%|<0hKBsAeCPE0^--KEw_KU>j{y$#JTga8brSQpgcb7?hLLkrOS5Z?iX3$esblO(K^hkyBV{)|M8^mQewZgU$+rAekliU3Dr^VvBXv()yS)L~VIsXMW09t(PW|AHVZhO?du$u*hG&|9g(~9?g7m*;!T4v+N$j5k;g$87Z~At}o4d?lZ*ZE=C0oTdPt!LBX7CpV=WRCem3`^`fqQ?u6$D&=@x~t^y4SG;mna4#UCG*-Drb+ea=Pvb^pt16)$~c(OnatmCw*k!u6eoTOO~)+j5HDJ1G!sT3db>9Cph=RCw48W(_uXRF0*Q7Zzpy5<$+VZkDcA(z)FcP=QHyW<F&k=&2d5M9Qeh8WIvU)-G%wWPPS8nz{{FL*xa8Tu*Z?uNz{pfN@^mz@*TfIF$yycI*89ZQq`=1zC70A4$WOVxQe@GmP{Fb<_+Ax?1>N)kL2s}RrLu>utz?2!GGU3Np`3I(M@A0a!l>ww?`8jNc~@7x=X_GVtlq+BFiZupknw|uxbwQR^@Nqav&3X1FjRlHXMR={ry+y}iNKP6J#(6|6JG+gG&1QgT(=2dcI?y;&N6tvFQTEkaVjHVnEFaYy99?lgi&@_#_XP42QT{ibnX4^9(EGi7)r=jsv&d?2wE3n4i4%fZ;H7)c71#9%NjIiYDftokz%c!A45TOh(J09q7W*D0=XkUoQI+GL*q%bgvh3oAP4)lLYkGY|70chB)J5s277?ePX>6$aRA6H-_G{>8UvDq7Fi{dj2kQ^@2l`PVia2ho%EB4+Kl_)4}Ct)s>QRTtr=uep-H#9B)jY<`IsfwWxA-AB5K1xW&R-5ek9<Oh}<ajm=Dm$}%tYdIp&`sUGWQ7M#I7dl}EtWm3FpoWkS09+ypOPMKXj}jqIK7CeF!Krn(nwJ>{$(_*K@6|YWmle|OF}d>D0?o*Aw)OSW}c=g=beAqUoO00PBoV?L%9H}Jb=c%8+sXNtboSak^F&?Jr!5NVODD_-g0GrbB$s8;8<hnRsfNX4n;^oYYG@hLRlm26x~Ex8)pp_+8&r!ymvz{1C6;`NGtjjo6vgYMIQFF?!gT<`|B;Q&TWQyflv({qEsAM!<JNVPOI3ymmT<!V!N-SqY4(}^~rnL@aMa>H#DwrhSEI*!ixXOf~q~dL@hi66vfox?L|2ck79M`3fAC*))-Q14KO4%fP@e>MGW^UcwWIF0L30a<K7Lu3^X8Wgf4AVXn^X}QEMP$a(1y=-e?UBnK{{{<AUA~?HfXkJ<LnmQ<p<)u&0f(WHO3`@2Sn_18Cg4p_hRM`Rv6;XLN)T?t(Qy5;i4R1J)ZEN*JKYQD>+stmAx3o&zU!*|ntYsZyB4A-wDuVQ6X|^y!NV@aNl3H#DvwLybhb&l$oJLT+fuTP}!<#g1<_%9XHbUQ3tkF;mCUrz-%qtcKRma46aHo>~Y=yE6^#wp#u)G|IgjdKqXGwi>cBltx`(8ZLGj%LqXl#$~)sI}P^|GQw6~8N%Kk_BDC{VF0Bfv<F(^9umZs8V{xIc~;h+g+?hU!|yg_><!Vs?IBoOd%w1?|M)Ne@*n@{AO26^@w)lzr)T}IhO78kU#&m=x#4QY=lU+*?-zs0gZ{54Kh76#g2k|gF)`T#qy!2rk76>dwVkORKIOmv*Z%=Km0D;"
_EMBEDDED_TOPOLOGY = "c-p;FO>5jR5dAB{=T)ea(k8xzH1x7Gh2&O>&`M)lRMLo%<l=_>_l~{WC5H_qkoIQAZ{Eku=&{LWgrL;~lpV&VYjjG46IfX=p~qpCQ!6dB(&&iM8SR@*V=-vApzr5cMkvk*7jq>Y4G29zEFv(tAh|d&eov~s+Ue{v_kAU1&tQdxfP$;wU4%{)L@#t)>K+DN*pmP|Ko&h=5Q$)NShLWzj7<J(k6@$D%o`C{hdB$1Pq(c&8Wzs7BiB0)c_wZ!_Kt$sL5~EYW_EleEKE4Tf$;3;9IRShG~KtyCSxT7%cz#1(s=DcmLK~IePy_Vz^|_I=n{i&uD9EJ^>BB$<$p!f0EMed&hF5;d}kR<>Ut<<RBO3;+Wbo;-nZ*#wa=*xCnVN*ThXNFzzloA!yFYCv6hoUSzhUPEnM)yy-sHh@hqH2{87`NaG7^n^IsIt|BoV)8Rhxz1GFzjy#9Rq<>9&FsWrSQb&VG2C*MB5Rr%hw=JN8Cz$w_PZjivbB6pQQ*L7;Cdaw3nMUasAF1|ng1|>9`kp"
_EMBEDDED_REPORT = "c-mD_%TB{U4Ez;q&k3SM<<J|C2qKkoXeAB^t(J`&EH>U~cathY{5wuUc^vJTu|4At^=7#8hl5T-i)yXPZMiS6Hv0N%e{-+*#cr=MRR`0)X{rP#j$JTpF}Kc86Y~iZj%nNAd#v<K?lDC2EQ%A5C*OMK>mlzKd4-GI8um=qI8i5`jMKykgRx138hhjv)q1&Fo!~?m7CKVR#!bj&rshgp-%acfwJn}>aeG&&_2PV)sfW==aVyp8LaK7NE4Ozi!e^$AKD-~CKk8_aO&}k2!kAFJin^f~iEE8jjq?ssWs1FU)cRSKzX!wjT@cWEjwy6jrobWi27a6ZaoZ)3$ia3Yh(nM}$PQ<c!Q*ShAVI-wW@7c|yrncigDH@eW<Zej|F?|l`>ru8?Vj)m6<QkO|K$@~*HtrhLp?%5hvU!z#?<9$lL?B@B3I&hBtC55)!27w!0CDL{a7$g{5GS5znYiNFQDkseg"


def unpack_snapshot(encoded):
    return json.loads(zlib.decompress(base64.b85decode(encoded)).decode("utf-8"))


def load_bundle():
    folder = Path(__file__).resolve().parent
    signals_path = folder / "de2_tier1_signals.json"
    topology_path = folder / "approved_topology.json"
    if signals_path.is_file() and topology_path.is_file():
        with signals_path.open(encoding="utf-8") as fh:
            signals = json.load(fh)
        with topology_path.open(encoding="utf-8") as fh:
            topology = json.load(fh)
        provenance = "External DE2 JSON files in this folder"
    else:
        signals = unpack_snapshot(_EMBEDDED_SIGNALS)
        topology = unpack_snapshot(_EMBEDDED_TOPOLOGY)
        provenance = "Bundled original DE2 JSON snapshot"
    report = unpack_snapshot(_EMBEDDED_REPORT)
    return signals, topology, report, provenance


def edge_key(obj):
    if "source_entity_id" in obj:
        return (
            obj["source_entity_id"],
            obj["relationship_type"],
            obj["target_entity_id"],
        )
    return (obj["source"], obj["relationship"], obj["target"])


def parse_time(raw):
    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def utc_label(raw):
    return parse_time(raw).astimezone(timezone.utc).strftime("%b %d, %Y · %H:%M:%S UTC")


def snapshot(signals, count):
    visible = signals[:count]
    matched, new, missing = set(), set(), set()
    counts = Counter()
    edge_counts = Counter()
    for item in visible:
        t = item["signal_type"]
        k = edge_key(item)
        counts[t] += 1
        edge_counts[(t, k)] += 1
        if t == "MATCHED":
            matched.add(k)
        elif t == "NEW_EDGE":
            new.add(k)
        elif t == "MISSING_EDGE":
            # A missing-edge record is an absence signal, not an observed edge.
            missing.add(k)
    return {
        "matched": matched,
        "new": new,
        "missing": missing,
        "counts": counts,
        "edge_counts": edge_counts,
        "blast_radius": len({e[2] for e in new}),
        "new_relationships": len(new),
        "affected_agents": len({e[0] for e in new}),
    }


def short_name(raw):
    labels = {
        "agent-orch-2b6e11": "Orchestrator",
        "agent-claims-7f3a9c": "Claims Agent",
        "agent-cs-9a01e3-v1": "Customer Support v1",
        "agent-cs-9a01e3-v2": "Customer Support v2",
        "agent-underwriting-4d1c88": "Underwriting Agent",
        "tool:claims-tools-mcp:fetch_claim": "Fetch Claim",
        "tool:claims-tools-mcp:verify_policy_coverage": "Verify Policy Coverage",
        "tool:payments-mcp:approve_payout": "Approve Payout",
        "tool:policy-tools-mcp:lookup_policy_status": "Lookup Policy Status",
        "tool:credit-bureau-mcp:pull_credit_report": "Pull Credit Report",
        "model:anthropic:claude-sonnet-5": "Claude Sonnet 5",
        "model:openai:gpt-4o": "GPT-4o",
    }
    return labels.get(raw, raw.split(":")[-1][:28])


def graph_svg(approved_edges, state, show_baseline=True):
    """Generate a dependency-free, read-only graph for the current cursor."""
    baseline = {edge_key(e) for e in approved_edges}
    all_links = (baseline if show_baseline else state["matched"]) | state["new"]
    graph_nodes = {node for src, _, dst in all_links for node in (src, dst)}
    agents = sorted((n for n in graph_nodes if n.startswith("agent-")),
                    key=lambda n: (0 if "orch-" in n else 1, short_name(n)))
    others = sorted((n for n in graph_nodes if not n.startswith("agent-")),
                    key=lambda n: (1 if n.startswith("model:") else 0, short_name(n)))
    h = max(520, (max(len(agents), len(others)) - 1) * 69 + 100)
    width = 870
    positions = {}
    for idx, n in enumerate(agents):
        positions[n] = (24, 47 + idx * (h - 94) / max(len(agents) - 1, 1))
    for idx, n in enumerate(others):
        positions[n] = (565, 47 + idx * (h - 94) / max(len(others) - 1, 1))

    q = html.escape
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {h}" '
             f'role="img" aria-label="Proposed and observed relationships" '
             'style="display:block;width:100%;max-width:100%;min-width:530px;height:auto;">',
             '<defs>',
             '<marker id="garr" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M1 1 L7 4 L1 7" fill="none" stroke="#65a78b" stroke-width="1.4"/></marker>',
             '<marker id="oarr" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M1 1 L7 4 L1 7" fill="none" stroke="#f59a39" stroke-width="1.4"/></marker>',
             '<marker id="barr" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M1 1 L7 4 L1 7" fill="none" stroke="#626c79" stroke-width="1.4"/></marker>',
             '</defs>',
             '<rect width="100%" height="100%" rx="8" fill="#0c1018"/>',
             '<text x="150" y="20" fill="#a5adbb" font-family="sans-serif" font-size="12">AI AGENTS</text>',
             '<text x="674" y="20" fill="#a5adbb" font-family="sans-serif" font-size="12">TOOLS / MODELS</text>']
    # Draw the expected links in subdued gray until they are observed in batch.
    for src, relation, dst in sorted(all_links, key=lambda e: e in state["new"]):
        if src not in positions or dst not in positions:
            continue
        sx, sy = positions[src]
        tx, ty = positions[dst]
        if src == dst:
            continue
        if dst.startswith("agent-"):
            x1, x2 = sx + 231, tx + 231
            y1, y2 = sy, ty
            path = f"M {x1:.1f} {y1:.1f} C 470 {y1:.1f}, 470 {y2:.1f}, {x2:.1f} {y2:.1f}"
        else:
            x1, x2 = sx + 231, tx
            y1, y2 = sy, ty
            path = f"M {x1:.1f} {y1:.1f} C 393 {y1:.1f}, 420 {y2:.1f}, {x2:.1f} {y2:.1f}"
        if (src, relation, dst) in state["new"]:
            stroke, dash, w, arr, status = "#f59a39", "", 3.4, "oarr", "NEW_EDGE observed"
        elif (src, relation, dst) in state["matched"]:
            stroke, dash, w, arr, status = "#65a78b", "", 2.5, "garr", "MATCHED observed"
        else:
            stroke, dash, w, arr, status = "#626c79", 'stroke-dasharray="6 6"', 1.6, "barr", "Proposed baseline (no signal yet)"
        lines.append(f'<path d="{path}" fill="none" stroke="{stroke}" '
                     f'stroke-width="{w}" opacity="0.82" {dash} marker-end="url(#{arr})">'
                     f'<title>{q(short_name(src))} → {q(short_name(dst))} | {q(relation)} | {status}</title>'
                     '</path>')

    for node, (x, y) in positions.items():
        is_model = node.startswith("model:")
        is_agent = node.startswith("agent-")
        fill = "#312a24" if is_model else "#1b3040" if is_agent else "#202936"
        border = "#f59a39" if is_model else "#6c8ca7" if is_agent else "#65788c"
        is_new_target = is_model and node in {e[2] for e in state["new"]}
        if is_new_target:
            border = "#f59a39"
        text = q(short_name(node))
        kind = "MODEL" if is_model else "AGENT" if is_agent else "TOOL"
        lines.append(f'<g><rect x="{x}" y="{y-20:.1f}" width="231" height="42" rx="7" '
                     f'fill="{fill}" stroke="{border}" stroke-width="1.5" />'
                     f'<title>{q(node)}</title>'
                     f'<text x="{x+12}" y="{y-3:.1f}" fill="#f1f5f9" font-family="sans-serif" font-size="12">{text}</text>'
                     f'<text x="{x+12}" y="{y+13:.1f}" fill="#aab9cb" font-family="sans-serif" font-size="9">{kind}</text>'
                     '</g>')
    lines.append('</svg>')
    return ''.join(lines), h


def assert_valid_bundle(records, topo):
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError("Signals JSON must be a list of signal objects.")
    if not isinstance(topo, dict) or not isinstance(topo.get("approved_edges"), list):
        raise ValueError("Topology must have an approved_edges list.")
    needed = {"event_id", "event_time", "source_entity_id", "relationship_type", "target_entity_id", "signal_type"}
    for idx, r in enumerate(records):
        if not needed.issubset(r):
            raise ValueError(f"Signal {idx} is missing required fields.")
        if r["signal_type"] not in ("NEW_EDGE", "MATCHED", "MISSING_EDGE"):
            raise ValueError(f"Signal {idx} has an unsupported type.")
        parse_time(r["event_time"])
    versions = {r.get("approved_graph_version") for r in records}
    if len(versions) > 1 or (versions and topo.get("schema_version") not in versions):
        raise ValueError("Signals and proposed topology have different versions.")


try:
    signal_rows, proposed_topology, de2_report, source_label = load_bundle()
    assert_valid_bundle(signal_rows, proposed_topology)
    signal_rows = sorted(signal_rows, key=lambda e: (parse_time(e["event_time"]), str(e["event_id"])))
except (OSError, ValueError, TypeError, KeyError) as exc:
    st.error(f"Cannot load DE2 replay: {exc}")
    st.stop()

max_index = len(signal_rows)
if not max_index:
    st.error("No signals are available to replay.")
    st.stop()

# Main handoff includes a November missing-edge record well after the August batch.
first_date = parse_time(signal_rows[0]["event_time"]).date()
main_end = max((i+1 for i, r in enumerate(signal_rows)
                if parse_time(r["event_time"]).date() == first_date), default=max_index)
late_missing_indices = [i+1 for i, r in enumerate(signal_rows)
                        if r["signal_type"] == "MISSING_EDGE"
                        and parse_time(r["event_time"]).date() != first_date]

if "insurance_replay_index" not in st.session_state:
    st.session_state["insurance_replay_index"] = 0
st.session_state["insurance_replay_index"] = min(
    max(0, st.session_state["insurance_replay_index"]), max_index
)

# Jump checkpoints are derived from first occurrences in actual events.
checkpoints = {"Baseline · before first signal": 0}
seen_new = set()
for index, event in enumerate(signal_rows, 1):
    e = edge_key(event)
    if event["signal_type"] == "NEW_EDGE" and e not in seen_new:
        seen_new.add(e)
        checkpoints[f"New relationship {len(seen_new)} · {short_name(e[0])} → {short_name(e[2])}"] = index
checkpoints["End of initial dated batch"] = main_end
for idx in late_missing_indices:
    checkpoints[f"Later missing-edge signal · {utc_label(signal_rows[idx-1]['event_time'])}"] = idx
checkpoints["All 256 signals · last record" if max_index == 256 else "All signals · last record"] = max_index

with st.sidebar:
    st.title("GUARDIUMONE")
    st.caption("AgentMonitor · Executive prototype")
    st.markdown("---")
    st.write("**Insurance Claims · DE2 Replay**")
    st.caption("One demonstration, no scenario selector")
    st.info("REPLAY MODE · Synthetic, previously generated ML signals. Not connected to live telemetry.")
    st.caption(f"Source: {source_label}")
    st.caption(f"Topology: {proposed_topology.get('schema_version', 'Unknown')}")
    st.warning("Baseline is proposed, not formally approved.")
    st.caption("No live token velocity, data sensitivity classification, or containment timestamps supplied.")

st.caption("ENTERPRISE AI GOVERNANCE / EXECUTIVE VIEW / HISTORICAL SYNTHETIC REPLAY")
st.title("AgentMonitor / Risk Overview")
st.markdown('<span class="gd-pill">UNVERIFIED · REVIEW</span>', unsafe_allow_html=True)
st.subheader("Unexpected AI model relationships in insurance operations")
st.caption("Insurance Claims Graph · DE2 Tier 1 · Synthetic monitoring batch")

st.divider()
st.subheader("Incident Replay")
st.caption("Step through recorded signals. The graph, KRIs, and evidence update from the selected event. No agent actions are executed.")

jump_names = list(checkpoints)
def jump_to_selected():
    st.session_state["insurance_replay_index"] = checkpoints[st.session_state["insurance_jump"]]

st.selectbox("Jump to key event", jump_names, key="insurance_jump", on_change=jump_to_selected)
prev_col, next_col, reset_col = st.columns(3)
with prev_col:
    if st.button("◀ Previous", width="stretch", disabled=st.session_state["insurance_replay_index"] == 0):
        st.session_state["insurance_replay_index"] -= 1
with next_col:
    if st.button("Next ▶", width="stretch", disabled=st.session_state["insurance_replay_index"] == max_index):
        st.session_state["insurance_replay_index"] += 1
with reset_col:
    if st.button("↺ Restart", width="stretch"):
        st.session_state["insurance_replay_index"] = 0
st.slider("Replay position (signals revealed)", min_value=0, max_value=max_index,
          key="insurance_replay_index", step=1)

cursor = st.session_state["insurance_replay_index"]
state = snapshot(signal_rows, cursor)
current_event = signal_rows[cursor-1] if cursor else None
st.caption(f"Signal {cursor} of {max_index} · " +
           (utc_label(current_event["event_time"]) if current_event else "Baseline — no observed signals displayed"))
if cursor > main_end:
    st.warning("This is a later, separately dated missing-edge signal (November 4), not a continuous continuation of the August 31 incident.")

st.divider()
st.subheader("Five Executive KRIs")
metrics = st.columns(5)
metrics[0].metric("BLAST RADIUS", f"{state['blast_radius']} resources")
metrics[1].metric("DATA SENSITIVITY", "Not provided")
metrics[2].metric("BOUNDARY DRIFT", f"{state['new_relationships']} new links")
metrics[3].metric("TOKEN VELOCITY", "Not measured")
metrics[4].metric("CONTAINMENT SLA", "Not measured")
st.caption("Blast Radius = count of distinct directly targeted resources in NEW_EDGE relationships revealed so far. "
           "New links represent distinct (source, relationship, target) triples, not signal totals. "
           "No containment event, SLA target, token rate, or data classification was provided.")

st.divider()
left, right = st.columns([1.45, 1])
with left:
    st.subheader("Proposed vs. Observed Interaction Graph")
    show_proposed = st.checkbox("Show all proposed baseline links", value=True)
    svg, height = graph_svg(proposed_topology["approved_edges"], state, show_proposed)
    components.html(
        '<div style="width:100%;height:100%;overflow:auto;background:#0c1018;">' + svg + '</div>',
        height=min(590, height + 12), scrolling=True,
    )
    st.caption("Green: matched baseline link · Orange: newly observed relationship · Dashed gray: proposed but not yet observed in this replay. Hover for IDs.")
    st.caption("The late MISSING_EDGE signal is evidence of an expected edge reported absent at that later time; it is not drawn as an observed connection.")
with right:
    st.subheader("Evidence Signals")
    if current_event is None:
        st.info("Baseline loaded. Choose Next to reveal the first recorded event.")
    else:
        kind = current_event["signal_type"]
        observed = kind != "MISSING_EDGE"
        st.markdown(f"**Detected activity:** `{kind}`")
        st.markdown(f"**Agent:** {short_name(current_event['source_entity_id'])}")
        st.markdown(f"**Target resource:** {short_name(current_event['target_entity_id'])}")
        st.markdown(f"**Relationship:** `{current_event['relationship_type']}`")
        st.markdown("**Observed relationship:** " + ("Yes — reported by Tier 1 signal" if observed else "No — missing-edge signal"))
        st.markdown("**Topology status:** " +
                    ("Not in proposed baseline" if kind == "NEW_EDGE"
                     else "Listed in proposed baseline"))
        st.markdown(f"**Event time:** {utc_label(current_event['event_time'])}")
        st.markdown(f"**Trace ID:** `{current_event.get('trace_id', 'Unavailable')}`")
        if kind == "MISSING_EDGE":
            st.warning("Do not interpret this as a proven disappearance of the link. The same triple had earlier MATCHED signals in the August batch.")
        elif kind == "NEW_EDGE":
            st.warning("New topology relationship detected; authorization and malicious intent are not established by this signal.")
        else:
            st.success("Relationship present in proposed topology and reported in a signal.")

    st.subheader("Executive Response Context")
    with st.expander("View suggested verification steps (demo operator only)"):
        st.write("Confirm whether the proposed topology is the approved policy baseline; "
                 "verify the owners and permissions of newly observed model relationships; "
                 "review underlying telemetry before determining whether restrictions or escalation are warranted.")
        st.caption("This is guidance, not an ML-generated containment recommendation.")

st.divider()
st.subheader("DE2 Signal Summary")
counts = state["counts"]
cols = st.columns(4)
cols[0].metric("Signals revealed", cursor)
cols[1].metric("MATCHED", counts["MATCHED"])
cols[2].metric("NEW_EDGE", counts["NEW_EDGE"])
cols[3].metric("MISSING_EDGE", counts["MISSING_EDGE"])
st.caption(f"Original full dataset: {max_index} detection signals. "
           "Signal count is not the same as distinct edge count or observed_count (which is unavailable).")

st.subheader("Verified Backend Component Evidence")
with st.expander("Show DE2 handoff report and topology version"):
    st.write("**Topology version:**", proposed_topology.get("schema_version", "Unavailable"))
    st.write("**Baseline approval:** Proposed demo baseline — not authoritative policy")
    st.write("**DE2 test report (original snapshot):**")
    st.json(de2_report)
    st.caption("A passing ML test is not evidence that this dashboard is connected to production telemetry.")

st.divider()
st.subheader("Trace Evidence · Structured JSON")
if current_event:
    st.json(current_event, expanded=True)
else:
    st.json({"replay_position": 0, "state": "PROPOSED_BASELINE_ONLY",
             "topology_version": proposed_topology.get("schema_version")})

export_state = {
    "mode": "SYNTHETIC_HISTORICAL_REPLAY",
    "source": source_label,
    "topology_version": proposed_topology.get("schema_version"),
    "topology_approval_status": "PROPOSED_NOT_CONFIRMED",
    "replay_signal_index": cursor,
    "replay_signal_total": max_index,
    "current_event": current_event,
    "direct_blast_radius_distinct_targets": state["blast_radius"],
    "unique_new_relationships": state["new_relationships"],
    "affected_agents_with_new_relationships": state["affected_agents"],
    "signal_counts_so_far": dict(state["counts"]),
    "unique_new_edges_so_far": [
        {"source": a, "relationship": r, "target": b}
        for a, r, b in sorted(state["new"])
    ],
    "data_sensitivity": None,
    "token_velocity": None,
    "containment_latency": None,
    "downstream_impact_assessed": False,
}
st.download_button("Export displayed replay evidence",
                   data=json.dumps(export_state, indent=2),
                   file_name="guardiumone_insurance_replay_evidence.json",
                   mime="application/json", width="stretch")
st.caption("Replay of synthetic signals. No production data, real-time monitoring, verified model permissions, confirmed compromise, or containment action.")
