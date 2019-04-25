
from tensorflow.keras import backend as K
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import *
from tensorflow.keras.utils import *
from tensorflow import keras
import losses
import numpy as np
def createLayers(input , outputSize , kernel_size=(4,4), strides=(2,2) ,leaky=True , batch=True):
    l = Conv2D(outputSize ,  kernel_size = kernel_size , strides=strides)(input)
    if leaky:
        l = LeakyReLU(.2)(l)
    if batch:
        l = BatchNormalization()(l)
    return l

#Generate label for target Y for the loss functions
#If 1 is generated then the target image was associated image was choosen

def labelGen(i):
    if i == 1:
        return 1.0
    return 0.0

class PLDTGAN:

    def __init__(self , input_shape , filters=64 ,epochs):
        self._epochs = epochs
        self._num_filters = filters
        self._input_shape = input_shape
        self.batch_size = 64
        self.GAN = self.createGAN(input_shape , self._num_filters)
        self.Discrm = self.createDisc(input_shape , self._num_filters)
        self.Assoc = self.createAssociated(input_shape , filters)


    def train(self, x,y):

        optimizer = keras.optimizers.SGD(learning_rate=1e-3)
        


        '''
            Train All 3 models at once 
        '''


        for epoch in range(self.epochs):
            
            for step, x_batch  in enumerate(x):
                
                #if the assocated image 
                t = np.array([ labelGen(np.random.randint(3)) for i in range(self.batch_size)])


                with tf.GradientTape() as GTape:
                    logits = self.GAN(x_batch)
                    
                    with tf.GradientTape() as DTape: 
                        DY = self.Discrm(x_batch)
                        loss_value = Assoc_Discrm_Loss(DY , t )
                    grads = DTape.gradient(loss_value , self.Discrm.trainable_variables)
                    self.opt.apply_gradients(zip(grads,self.Discrm.trainable_variables))

                    with tf.GradientTape() as ATape:
                        #need to cat the images
                        
                        AY = self.Assoc(x_batch)
                        loss_value = Assoc_Discrm_Loss(DY , t)
                    grads = ATape.gradient(loss_value , self.Assoc.trainable_variables )
                    self.opt.apply_gradients(zip(grads,self.Assoc.trainable_variables)) 

                    loss_value = GANLoss(DY, AY)
                    grads = GTape.gradient(loss_value , self.GAN.trainable_variables)
                    self.opt.apply_gradients(zip(grads,self.GAN.trainable_variables))

    def test(self, x,y):
        pass

    '''
        Helper Functions to create network
    '''   

    def createGAN(self , input_shape , filters):

        def createInGenLayer(inLayer , outputSize , norm=True , kernel_size=(4,4) , strides=(2,2)):
            l = Conv2D(outputSize , kernel_size = kernel_size , strides=strides)(inLayer)
            l = LeakyReLU(.2)(l)
            if norm:
                l = BatchNormalization()(l)
            return l
        def createOutGenLayer(inLayer , outputSize , activation='relu' , norm=True , kernel_size=(4,4) , strides=(2,2)):
            l = Conv2DTranspose(outputSize , activation=activation , kernel_size=kernel_size , strides=strides)(inLayer)
            if norm:
                l = BatchNormalization()(l)
            return l
        
        in_layer = Input(shape=input_shape , name = "Input")

        G1 = createInGenLayer(in_layer , filters)
        G2 = createInGenLayer(G1 , filters * 2)
        G3 = createInGenLayer(G2, filters * 4)
        G4 = createInGenLayer(G3 , filters * 8)

        G5 = createOutGenLayer(G4 , filters * 4)
        G6 = createOutGenLayer(G5 , filters * 2)
        G7 = createOutGenLayer(G6 , filters)
        G8 = createOutGenLayer(G7 , 3 , activation='tanh')

        GenModel = Model(inputs=[in_layer] , outputs=[G8])
        #GenModel.compile(loss='mean_squared_error', optimizer='sgd')

        return GenModel

    def createDisc(self , input_shape , filters ):

        in_layer = Input(shape=input_shape , name="Discrm_Input")
        L1 = createLayers(in_layer , filters)
        L2 = createLayers(L1 , filters * 2)
        L3 = createLayers(L2 , filters * 4)
        L4 = createLayers(L3 , filters * 8)
        L5 = createLayers(L4 , 1 , kernel_size=2, strides=1 ,leaky=False , batch=False)
        L6 = Activation('sigmoid')(L5)
        
        DiscModel = Model(inputs=[in_layer] , outputs=[L6])
       #DiscModel.compile(loss='mean_squared_error', optimizer='sgd')
        

        return DiscModel

    def createAssociated(self , inputs , filters):

        image1 = Input(shape=inputs , name="Image_1")       
        image2 = Input(shape=inputs , name="Image_2")       
        
        InCat = Concatenate()([image1 , image2])
        L1 = createLayers(InCat , filters)
        L2 = createLayers(L1 , filters * 2)
        L3 = createLayers(L2 , filters * 4)
        L4 = createLayers(L3 , filters * 8)
        
        L5 = createLayers(L4 , 1 ,  kernel_size=2, strides=1 , leaky=False , batch=False)
        L6 = Activation('sigmoid')(L5)
        
        AssocModel = Model(inputs=[image1,image2] , outputs=L6 )
        #AssocModel.compile(loss='mean_squared_error', optimizer='sgd')
        
        return AssocModel