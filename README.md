# FluidMechanics
Simple yet effective algorithms for flow simulation

# 1) Make application
        eb init -p python 3.6 generative-design --region eu-central-1
        eb init
        eb create generative-design-env --elb-type application -im 1 -ix 1 -i t2.small

# 2) Terminate Env
        eb terminate generative-design-env
