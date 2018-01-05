# greengrass_robot_arm_sample

　AWS Greengrass の公式ドキュメントで紹介されているロボットアームのシナリオをそのまま動かしてみましたが、手順をそのままトレースしただけだったので、内容の理解のためにも Python 版の SDK を使ってデバイス用コードを実装してみました。

　具体的には、グループやサブスクリプション等の設定は公式ドキュメントの手順のものをそのまま使用し、 RobotArm_Thing と Switch_Thing で動かすプログラムを、 AWS IoT C++ Device SDK のサンプルとして提供されていたものと同じものを AWS IoT Device SDK for Python を使用して実装しています。

　下記ブログで解説しています。  
　http://blog.akanumahiroaki.com/entry/2018/01/05/090000
