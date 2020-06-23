#!/usr/bin/env python
import smbus                    #smbusライブラリ扱う(i2c通信）
import time                     #システムの時間を扱う
import numpy as np              #配列を扱う関数
import matplotlib.pyplot as plt #グラフを作成する関数
import csv                      #CSVモジュールを扱う
import datetime                 #日付、時間を扱う

i2c = smbus.SMBus(2)            # Get I2C bus
addr=0x5a                       # slave address:5a hex
                                          
def crc8atm(data) :    # data=0x87654321    0b10000111011001010100001100100001 2進数変換  
        data =data <<8 # dataを8左シフト    0b1000011101100101010000110010000100000000 (初期値を付加する0x00=00000000,40bit)
        length = len(bin(data)[2:])    #      10000111011001010100001100100001 [2:]...リスト2スライス,0b削除
        for i in range(length):                 # lenghtを繰り返す
            if int(bin(data)[2:3],2) == 1 :     # MSB =1,   上位bitが1であるか確かめる
                nokori = bin(data)[11:]         #      11001010100001100100001 [11:]..リスト11スライス
                #  100001110
                #  100000111  XOR:排他的論理和(aまたはbが1の場合bit:1)
                #  000001001  XOR後のDATA  
                sentou = (int(bin(data)[2:11],2)) ^ (int('100000111',2)) # crc-8=x8+x2+x1+1=100000111
                #  0000010011100101010000110010000100000000  (sentou+nokori)
                #       100000111                            XOR:排他的論理和(aまたはbが1の場合bit:1)
                #       00011111001010000110010000100000000  XOR後のDATA
                data = int((str(bin(sentou)[2:11])+str(nokori)),2)
                # dataを2進数から整数にする
                data=int(bin(data),2)
                # 0111010010
                #  100000111  XOR:排他的論理和(aまたはbが1の場合bit:1)
                #  011010101 <9(9より小さい)
            if len(str(bin(data)[2:]))<9:
                #  011010101 =0xd5      
                return(hex(data))
#main
# i2c.write_i2c_block_data(addr,0x25,[0xb4,0xb7,0x75]) # default
# addrの0x5a=01011010は 1bit左にシフトして、write:10110100=0xb4,read:10110101=0xb5
# write word:[slave adress] [commnd] [data byte low] [data byte high] [pec]

# PWMCTRL:0b1000000001, 0bit:シングルPWM(1),1bit:smbus有効(0),2bit:open drain方式(0)
# 15bit:pwm周期設定,  周期はt=1.024*p[ms],15bit=64, 1.024*64=65.536[ms]
print (bin(i2c.read_word_data(addr,0x22)) ,"PWMCTRL")
# Config Register1:0b1011011101110101 15bit:sensor test無効(1)
# 11~13bit:GAIN=100(110),8~10bit:FIRフィルター=1024(111),
# 6bit:single IR sensor(1),4~5bit:赤外線温度tobj1,赤外線温度tobj2(11) 0~2bit:IIR係数ディジタルフィルタ,a1=0.8,b1=0.2,(101)
print (bin(i2c.read_word_data(addr,0x25)) ,"Config Register1")
# addr=0x5a
print (hex(i2c.read_byte_data(addr,0x2e)) ,"slave address")
time.sleep(0.5)

#リスト作成,timecount作成
Ambient_tempdata=[]
interval=[]
Object_tempdata=[]
timecount=0

try:                                        # 例外が発生する可能性がある処理
    index=1
    while index <= 5:                      # index 「1」「2」「3」...と1から順に番号が割り当て,繰り返し回数   
        timestamp = datetime.datetime.now() # 現在の日付、現在時刻の取得,スタンプ
        print(timestamp)                    # timestampを出力する
        Atemp = i2c.read_word_data(addr,0x6) # addr:0x5a,レジスタアドレス:0x6(周辺温度),3byte(下位data,上位data,crc)
        Otemp1 = i2c.read_word_data(addr,0x7)# addr:0x5a,レジスタアドレス:0x7(赤外線温度tobj1),3byte(下位data,上位data,crc)
        print (Atemp)
        print (hex(Atemp))
        print (type(Atemp))
        print (Otemp1)
        print (hex(Otemp1))
        print (type(Otemp1))
        # Otemp2 = i2c.read_i2c_block_data(addr,0x8,3)
        # [1]*256=上位桁上げ0~255(256通り),摂氏℃に直すには、0.02を掛けて273.15を引きます。
        # 絶対温度(ケルビン)T(K)＝t(℃)＋273.15,  t(℃)=T(K)-273.15,分解能0.02を乗算します
        #AmbientTemp = ((Atemp[1]*256 + Atemp[0]) *0.02 -273.15)
        AmbientTemp = (Atemp*0.02 -273.15)
        #ObjectTemp1 = ((Otemp1[1]*256 + Otemp1[0]) *0.02 -273.15)
        ObjectTemp1 = (Otemp1*0.02 -273.15)
        # ObjectTemp2 = ((Otemp2[1]*256 + Otemp2[0]) *0.02 -273.15)
        # 周囲温度,測定温度を出力する
        print (round(AmbientTemp,2))
        print (round(ObjectTemp1,2))
        print (round(AmbientTemp,2),round(ObjectTemp1,2))
        # チップから測定した周囲温度,(Atemp下位dataの16進数,Atemp上位dataの16進数,読み込んだCRCの16進数)
        #print ("TempHEXAdata",hex(Atemp[0]),hex(Atemp[1]),"readedCRC",hex(Atemp[2]),)
        # Atemp下位dataを16進数します,[2:]スライスで0xを除去します。,Atemp上位dataを16進数します,[2:]スライスで0xを除去します。
        # Atemp下位data+Atemp上位dataの16進数を整数にします
        #data = int((hex(int("b406b5"+str(hex(Atemp[0])[2:])+str(hex(Atemp[1])[2:]),16)) ),16)
        #print (crc8atm(data)),"<-calculated"        
        
        timecount += 1                    # timecountを1増やす
        # indexへAmbient_tempdata,interval,Object_tempdataを追加する
        Ambient_tempdata.append(round(AmbientTemp,2))  
        interval.append(timecount)
        Object_tempdata.append(round(ObjectTemp1,2))
        # dataへtimestamp,timecount,AmbientTemp,2,ObjectTemp1,2を入力する
        data = [timestamp,timecount,round(AmbientTemp,2),round(ObjectTemp1,2)]
        # data,("-----")を出力する
        print('data',data)
        print('-----')
        # hikaru.csvファイルへ改行し、行を詰めて書き込みます
        # newlineはファイルの改行コードを指定する引数です
        # dataへ書き込みます
        writer = csv.writer(open('hikaru.csv','a',newline=''))
        writer.writerow(data)
        # indexへ+１増やします
        index += 1
        # cpuに0.85秒間while処理を停止させ、他の処理をさせる　これがないと計算処理に大半を費やす
        time.sleep(0.85)

except KeyboardInterrupt: # 例外を受けて実行する処理,keybordのctrl+c処理でこのブロックへ移る
    pass                  # 何もせずに、次に移るという意味

fig, ax1 = plt.subplots() #折れ線のサブプロットの図を作成
ax2 = ax1.twinx()         # 2つのプロットを関連付ける
ax1.plot(interval,Ambient_tempdata,marker="o", color = "red", linestyle = "--" ,label = "Ambien_temp[c]" ) # グラフを描く
ax2.plot(interval,Object_tempdata,marker="o", color = "green", linestyle = "-.",label = "Object_temp[c]")  # グラフを描く
plt.title("temp")                 # タイトル
ax1.set_xlabel("time")            # x軸のラベル
ax1.set_ylabel("Ambien_temp[c]")  # y1軸のラベル
ax2.set_ylabel("Object_temp[c]")  # y2軸のラベル
ax1.legend(loc = "upper center")  # 凡例を作る
ax2.legend(loc = "upper right")   # 凡例を作る
ax2.grid(True)                    # ax2のグリット
plt.savefig("/home/pi/temp_mlx90614-diy.png")
plt.xlim()                        # x軸の範囲
ax1.set_ylim(20,30)               # y1軸の範囲
ax2.set_ylim(20,40)               # y2軸の範囲
plt.show()                        # 表示する
# index.htm-mlx90614-diyへ周囲温度,測定温度,タイムスタンプを書き込み
f = open('index.htm-mlx90614-diy','w') 
f.write(str(Ambient_tempdata) +"c "+str(Object_tempdata) +"c,"+str(timestamp))
# ファイルを閉じる
f.close()



