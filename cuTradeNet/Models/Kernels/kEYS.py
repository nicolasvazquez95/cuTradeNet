from numba import cuda
from numba.cuda.random import xoroshiro128p_uniform_float32

#Kernels for the Monte Carlo Simulation Extended Yard Sale

@cuda.jit
def gpu_MCS(Nw,Nr,SI,SJ,f,wmin,L1,L2,rng_states,M,N,Na):
    
    #get thread id and block id
    idx=cuda.threadIdx.x 
    bidx=cuda.blockIdx.x
   
    #get the index of the agent
    if idx<N and bidx<Na:
        i=bidx*N+idx

        if L2[i+1]-L2[i]==0: #check neighbors 
            SI[i]=0 #free

        else:
            for m in range(M):
                #choose a random neighbor
                j=L1[L2[i]:L2[i+1]][int(xoroshiro128p_uniform_float32(rng_states, i)*(L2[i+1]-L2[i]))]

                #START (kind of) mutex lock

                SI[i]=1 #indicate the thread is still active
                SJ[i]=j #indicate j neighbor to exchange to other threads
                cuda.syncthreads() #wait for all threads to load their status

                for i2 in range(bidx*N,i): #check if i2 is already locked
                    while(cuda.atomic.compare_and_swap(SI[i2:i2+1],-1,10)): #impossible CAS to read the value atomically
                        #Check j (i's neighbor) is i2 or i is i2's neighbor or j (i's neighbor) is i2's neighbor
                        if(i2==j or SJ[i2]==i or SJ[i2]==j): 
                            continue #wait 
                        break #next i2
                
                #END (kind of) mutex lock

                #get wealths
                wi=Nw[i] 
                wj=Nw[j]

                if wi>wmin and wj>wmin: #check if wealths are above the minimum

                    #START Yard-Sale exchange

                    if wi*Nr[i]<wj*Nr[j]:
                        dw=wi*Nr[i]
                    else:
                        dw=wj*Nr[j]
                    
                    #calculate probability of exchange with the wealth difference and f
                    pn=0.5+f*(wj-wi)/(wi+wj)
                    x=pn/(1-pn)
                    n=int(bool(int(xoroshiro128p_uniform_float32(rng_states, i)*(1+x))))
                    
                    #perform exchange
                    if n:
                        Nw[i]=Nw[i]+dw
                        Nw[j]=Nw[j]-dw
                    else:
                        Nw[i]=Nw[i]-dw
                        Nw[j]=Nw[j]+dw

                    #END Yard-Sale exchange
                
                SI[i]=0 #free
                cuda.syncthreads() #wait for all threads to load their status


        
@cuda.jit
def gpu_MCSepoch(Nw,Nr,SI,SJ,f,wmin,L1,L2,rng_states,M,N,Na,Wis):
    
    #get thread id and block id
    idx=cuda.threadIdx.x 
    bidx=cuda.blockIdx.x

    #get the index of the agent
    if idx<N and bidx<Na:
        i=bidx*N+idx
    
        if L2[i+1]-L2[i]==0: #check neighbors
            SI[i]=0 
            cuda.atomic.add(Wis[i:i+1],0,Nw[i]*M) #add wealth to the wealth index

        else:
            for m in range(M):
                #choose a random neighbor
                j=L1[L2[i]:L2[i+1]][int(xoroshiro128p_uniform_float32(rng_states, i)*(L2[i+1]-L2[i]))]

                #START (kind of) mutex lock

                SI[i]=1 #indicate the thread is still active
                SJ[i]=j #indicate j neighbor to exchange to other threads
                cuda.syncthreads() #wait for all threads to load their status
                
                for i2 in range(bidx*N,i): #check if i2 is already locked
                    while(cuda.atomic.compare_and_swap(SI[i2:i2+1],-1,10)): #impossible CAS to read the value atomically
                        #Check j (i's neighbor) is i2 or i is i2's neighbor or j (i's neighbor) is i2's neighbor
                        if(i2==j or SJ[i2]==i or SJ[i2]==j): 
                            continue #wait
                        break #next i2
                            
                #END (kind of) mutex lock

                #get wealths
                wi=Nw[i] 
                wj=Nw[j]

                if wi>wmin and wj>wmin: #check if wealths are above the minimum

                    #START Yard-Sale exchange

                    if wi*Nr[i]<wj*Nr[j]:
                        dw=wi*Nr[i]
                    else:
                        dw=wj*Nr[j]

                    #Calculate probability of exchange with the wealth difference and f
                    pn=0.5+f*(wj-wi)/(wi+wj)
                    x=pn/(1-pn)
                    n=int(bool(int(xoroshiro128p_uniform_float32(rng_states, i)*(1+x))))

                    #perform exchange
                    if n:
                        Nw[i]=Nw[i]+dw
                        Nw[j]=Nw[j]-dw
                    else:
                        Nw[i]=Nw[i]-dw
                        Nw[j]=Nw[j]+dw

                    #END Yard-Sale exchange
                
                SI[i]=0 #free
                cuda.syncthreads() #wait for all threads to load their status

                #add wealth to the wealth index
                cuda.atomic.add(Wis[i:i+1],0,Nw[i])



@cuda.jit
def gpu_MCSfollow(Nw,Nr,SI,SJ,f,wmin,L1,L2,rng_states,M,N,Na,Wis,agent):
    
    #get thread id and block id
    idx=cuda.threadIdx.x 
    bidx=cuda.blockIdx.x

    #get the index of the agent
    if idx<N and bidx<Na:
        i=bidx*N+idx
    
        if L2[i+1]-L2[i]==0: #check neighbors
            SI[i]=0 

        else:
            for m in range(M):
                #choose a random neighbor
                j=L1[L2[i]:L2[i+1]][int(xoroshiro128p_uniform_float32(rng_states, i)*(L2[i+1]-L2[i]))]

                #START (kind of) mutex lock

                SI[i]=1 #indicate the thread is still active
                SJ[i]=j #indicate j neighbor to exchange to other threads
                cuda.syncthreads() #wait for all threads to load their status

                for i2 in range(bidx*N,i): #check if i2 is already locked
                    while(cuda.atomic.compare_and_swap(SI[i2:i2+1],-1,10)): #impossible CAS to read the value atomically
                        #Check j (i's neighbor) is i2 or i is i2's neighbor or j (i's neighbor) is i2's neighbor
                        if(i2==j or SJ[i2]==i or SJ[i2]==j): 
                            continue #wait
                        break #next i2
                            
                #END (kind of) mutex lock

                #get wealths
                wi=Nw[i] 
                wj=Nw[j]

                if wi>wmin and wj>wmin: #check if wealths are above the minimum

                    #START Yard-Sale exchange

                    if wi*Nr[i]<wj*Nr[j]:
                        dw=wi*Nr[i]
                    else:
                        dw=wj*Nr[j]

                    #Calculate probability of exchange with the wealth difference and f
                    pn=0.5+f*(wj-wi)/(wi+wj)
                    x=pn/(1-pn)
                    n=int(bool(int(xoroshiro128p_uniform_float32(rng_states, i)*(1+x))))

                    #perform exchange
                    if n:
                        Nw[i]=Nw[i]+dw
                        Nw[j]=Nw[j]-dw
                    else:
                        Nw[i]=Nw[i]-dw
                        Nw[j]=Nw[j]+dw

                    #END Yard-Sale exchange
                
                SI[i]=0 #free
                cuda.syncthreads() #wait for all threads to load their status

                #add wealth to the wealth index of the agent 'agent'
                if i==agent:
                    Wis[m]=Nw[i]