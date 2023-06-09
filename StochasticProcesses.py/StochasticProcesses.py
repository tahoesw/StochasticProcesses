'''
Created on 2011-07-29

@author: Cameron Davidson-Pilon 
@email: cam.davidson.pilon@gmail.com
@Project Homepage: http://code.google.com/p/stochastic-processes/  for documentation and examples
@My homepage: 70percentfatfree.com


Feel free to use this under the MIT license. 
Feel free to use and abuse this code, but please give me or the project the credit we deserve.



'''
from math import *
import random
import scipy.stats as stats
from scipy.special import *




class Step_process(object):
    """
      This is the class of finite activity jump/event processes (eg poisson process, renewel process etc). For this library, I will use
     the terms "jump" and "event" interchangeably. 
    """

    def  __init__(self, dict):
        "'dict' contains the time and space constraints"
        try:
            self.startTime = dict["startTime"]
            self.startPosition = dict["startPosition"]
            self.conditional=False
            if dict.has_key("endTime"):
                self.endTime = dict["endTime"]
                self.endPosition = dict["endPosition"]
                self.conditional=True
        except KeyError:
            print "Missing constraint in initial\end value dictionary. Check spelling?"
            
    def _check_time(self,t):
        if t<self.startTime:
            print "Attn: inputed time not valid (check if beginning time is less than startTime)."
            
                
    def generate_sample_path(self,times):
        self._check_time(times[0])
        return self._generate_sample_path(times)
    
    
    def generate_sample_jumps(self,T):
        self._check_time(T)
        return self._generate_sample_jumps(T)
    
    def get_mean(self,t):
        self._check_time(t)
        return self._get_mean(t)
    
    def get_variance(self,t):
        self._check_time(t)
        return self._get_variance(t)
    
    def get_mean_number_of_jumps(self,t):
        self._check_time(t)
        return self._get_mean_number_of_jumps(t)
    
    def generate_position_at(self,t):
        self._check_time(t)
        return _generate_position_at(t)
    
    def _get_mean_number_of_jumps(self,t):
        self._check_time(t)
        print "Attn: performing MC simulation"
        N=10000
        sum=0.0
        for i in range(N):
            n=0
            sum_t=self.T.rvs()
            while sum_t<t:
                n+=1
                sum_t+=self.T.rvs()
            sum+=n
        return sum/N

class Renewal_process(Step_process):
    """
    parameters:
    {T:see below, J:see below}
    
    T is a scipy "frozen" random variable object, from the scipy.stats library, that has the same distribution as the inter-arrival times 
    i.e. t_{i+1} - t_{i} equal in distribution to T, where t_i are jump/event times.
    T must be a non-negative random variable, possibly constant. The constant case in included in this library, see the Constant class in the auxillary
    functions and class at the bottom. 
    
    J is a scipy "frozen" random variable object that has the same distribution as the jump distribution. It can have any real support. Ex: for the poisson process,
    J is equal to 1 with probability 1, but for the compound poisson process J is distributed as a non-constant.
    
    Ex:
    import scipy.stats as stats
    
    #create a standard poisson process
    
    parameters = {"J":Constant(1), "T"=stats.Poisson(lambda)}}
    RnPs= Renewal_process(parameters)
      
    """
    def __init__(self, parameters, time_space_constraints):
        super(Renewal_process, self).__init__(time_space_constraints)
        self.T = parameters["T"]
        self.J = parameters["J"]
        self.rate = 1/self.T.mean()
        
    def forward_recurrence_time_pdf(self,x):
        "the forward recurrence time RV is the time need to wait till the next event, after arriving to the system at a large future time"
        return self.rate*self.T.sf(x)
    
    def backwards_recurrence_time_pdf(self,x):
        "the backwards recurrence time is the time since the last event after arriving to the system at a large future time"
        return self.forward_recurrence_time_pdf(x)
    
    def forward_recurrence_time_cdf(self,x):
        "the forward recurrence time RV is the time need to wait till the next event, after arriving to the system at a large future time"
        return int.quad(self.forward_recurrence_time_pdf, 0, x)
    
    def backward_recurrence_time_cdf(self,x):
        "the backwards recurrence time is the time since the last event after arriving to the system at a large future time"
        return int.quad(self.forward_recurrence_time_pdf, 0, x) 
    
    def spread_pdf(self,x):
        """the RV distributed according to the spread_pdf is the (random) length of time between the previous and next event/jump
         when you arrive at a large future time."""
        try:
            return self.rate*x*self.T.pdf(x)
        except AttributeError:
            return self.rate*x*self.T.pmf(x)
    
    def _generate_sample_path(self,times):
        pathOfJumps = self.generate_sample_jumps(times[-1])
        count=0
        path=[]
        N=len(pathOfJumps)
        #what happens when no jumps occur? KK done.
        try:
            tao = pathOfJumps[0][0]
        except IndexError:
            tao = times[-1]
        x = self.startPosition
        for t in times:
            if t<tao:
                path.append((t,x))
            else:
                while t>tao and count<N-1:
                    count+=1
                    tao=pathOfJumps[count][0]
                    x = pathOfJumps[count-1][1]
                
                path.append((t,x))
        return path
        
    def _generate_sample_jumps(self,T):
        "T-self.startTime is the time window we are looking for jumps in."
        t = self.startTime
        x = self.startPosition
        
        tao = self.T.rvs()
        delta = self.J.rvs()
        t=t+tao
        x = x + delta
        while t<T:
            path.append((t,x))     
            tao = self.T.rvs()
            delta = self.J.rvs()
            t=t+tao
            x = x + delta
        return path
    
    def _get_mean(self,t):
        return self.J.mean()*self.get_mean_number_of_jumps(t)
    
    def _generate_position_at(self,t):
        tao = self.startTime + self.T.rvs()
        x = self.startPosition
        while tao<t:
            x += self.X.rvs()
            tao += self.T.rvs()
        return x
            
class Poisson_process(Renewal_process):
    """
    This class creates the Poisson process defined by N(t) being distributed according to a poisson distribution. 
    parameters:
    {rate: scalar>0}
    """
    
    def __init__(self,parameters,time_space_constraints):
       self.rate = parameters["rate"]
       self.Exp = stats.expon(1/self.rate)
       self.Con = Constant(1) 
       super(Poisson_process,self).__init__({"J":self.Con, "T":self.Exp}, time_space_constraints)
       self.Poi = stats.poisson
       self.Bin = stats.binom
       
    def _get_mean(self,t):
        return self.startPosition + self.rate*(t-self.startTime)
    
    def _get_variance(self,t):
        return self.rate*(t-self.startTime)
    
    def _generate_sample_jumps(self,T):
        p = self.Poi.rvs(self.rate*(T-self.startTime))
        x = self.startPosition
        path=[]
        array = [self.startTime+(T-self.startTime)*random.random() for i in range(p)]
        array.sort() 
        for i in range(p):
            x+=1
            path.append((array[i],x))
            i+=1
        return path
    
    def _generate_position_at(self,t):
        if self.conditional:
            return self.Bin.rvs(self.endPosition, t/self.endTime)+self.startPosition
        else:
            return self.Poi.rvs(self.rate*(t-self.startTime))+self.startPosition

class Marked_poisson_process(Renewal_process):
    """
    This class constructs marked poisson process ie at exponentially distributed times, a 
    uniform RV is generated.
    
    parameters:
    {rate:scalar>0, U:scalar, upper-bound , L:scalar, <U, lower-bound, startTime:scalar}
    *the bounds refer to the uniform distribution
    
    Note there are no other time-space constraints
    """
    def __init__(self, parameters):
        self.L = parameters["L"]
        self.U = parameters["U"]
        self.startTime = parameters["startTime"]
        self.rate = parameters["rate"]
        self.Uni = stats.uniform()
        self.Poi = stats.poisson
        
    def generate_marked_process(self,T):
        process = []
                
        p = self.Poi.rvs(self.rate*(T-self.startTime))
        path=[]
        array = [self.startTime+(T-self.startTime)*random.random() for i in range(p)]
        array.sort() 
        for i in range(p):
            x = self.L+(self.U-self.L)*self.Uni.rvs()
            path.append((array[i],x))
            i+=1
        return path
        

class Compound_poisson_process(Renewal_process):
    """
    parameters:
    {"J":see below, "rate":scalar>0}
     J is a frozen scipy.stats random variable obj. It can have any support.
     Ex:
     import stats.scipy as stats
     
     Nor = stats.normal(0,1)
     cmp = Compound_poisson_process({"J":Nor}) 
    
    """
    def __init__(self, parameters,time_space_constraints):      
        self.J = parameters["J"]
        self.rate=parameters["rate"]
        self.Exp = stats.expon(1/self.rate)
        super(Compound_poisson_process, self).__init__({"J":self.J, "T":self.Exp}, time_space_constraints)
        self.Poi = stats.poisson
        
    def _get_mean(self,t):
        return self.startPosition + self.rate*(t-self.startTime)*self.J.mean()
    
    def _get_variance(self,t):
        return self.rate*(t-self.startTime)*(self.J.var()-self.J.mean()**2)
    
    def _generate_sample_jumps(self,T):
        p = self.Poi.rvs(self.rate*(T-self.startTime))
        x = self.startPosition
        path=[]
        array = [self.startTime+(T-self.startTime)*random.random() for i in range(p)]
        array.sort() 
        for i in range(p):
            x+=self.J.rvs()
            path.append((array[i],x))
            i+=1
        return path



class Diffusion_process(object):
    #
    #    Class that can be overwritten in the subclasses:
    #        _get_position_at(t)
    #        _get_mean_at(t)
    #        _get_variance_at(t)
    #        _generate_position_at(t)
    #        _generate_sample_path(times)
    #
    #    Class that should be present in subclasses:
    #
    #        _transition_pdf(x,t,y)
    #
    #
    
    def __init__(self, dict):
        "'dict' contains the time and space constraints"
        try:
            self.startTime = dict["startTime"]
            self.startPosition = dict["startPosition"]
            self.conditional=False
            if dict.has_key("endTime"):
                self.endTime = dict["endTime"]
                self.endPosition = dict["endPosition"]
                self.conditional=True
        except KeyError:
            print "Missing constraint in initial\end value dictionary. Check spelling?"
        self.Nor = stats.norm()

    
    def transition_pdf(self,t,y):
        self._check_time(t)
        "this method calls self._transition_pdf(x) in the subclass"
        try:
            if not self.conditional:
                return self._transition_pdf(self.startPosition, t-self.startTime, y)
            else:
                return self._transition_pdf(self.startPosition, t-self.startTime, y)*self._transition_pdf(y, self.endTime-t, self.endPosition)\
                        /self._transition_pdf(self.startPosition,self.endTime - self.startTime, self.endPosition)
        except:
            print "Attn: transition density is not defined"

    def expected_value(self,f,t,N):
        self._check_time(t)
        "uses a monte carlo approach to evaluate the expected value of the process f(X_t). N is the number of iterations. The parameter f\
        is a univariate python function."
        print "Attn: performing a Monte Carlo simulation..."
        if not self.conditional:
            sum=0
            for i in range(N):
                sum+=f(self.generate_position_at(t))
            return sum/N
        else:
            #This uses a change of measure technique.
            sum=0
            self.conditional=False
            for i in range(N):
                X = self.generate_position_at(t)
                sum+=self._transition_pdf(X,self.endTime-t,self.endPosition)*f(X)
            self.conditional=True
            return sum/(N*self._transition_pdf(self.startPosition, self.endTime-self.startTime, self.endPosition))
        
    def generate_position_at(self,t):
        self._check_time(t)
        "if _get_position_at() is not overwritten in a subclass, this function will use euler scheme"
        return self._generate_position_at(t)
        
    
    def get_mean_at(self,t):
        self._check_time(t)
        return self._get_mean_at(t)
    
    
    def get_variance_at(self,t):
        self._check_time(t)
        return self._get_variance_at(t)
    
    def generate_sample_path(self,times):
        try: #the time array might be empty
            self._check_time(times[0])
        except IndexError:
            pass
        return self._generate_sample_path(times)
    
    
    def _generate_sample_path(self,times):
        return self.Euler_scheme(times)
    
    def _get_variance_at(self,t):
        var = SampleVarStat()
        for i in range(10000):
            var.push(self.generate_position_at(t))
        return var.get_variance()
    
    
    def _get_mean_at(self,t):
        "if _get_mean_at() is not overwritten, then we use MC methods; 100000 iterations"
        def id(x):
            return x
        return self.expected_value(id, t, 100000)
    
    def _generate_position_at(self,t,delta=0.001):
        return self.Euler_scheme([t])[0][0]
        
    def _transition_pdf(self,x,t,y):
        print "Attn: transition pdf not defined"
    
    def _check_time(self,t):
        if t<self.startTime:
            print "Attn: inputed time not valid (check if beginning time is less than startTime)."
    
    def Euler_scheme(self,times,delta=0.001):
        "returns an array!"
        "The process needs the methods drift() and diffusion() defined."
        print "Attn: starting a Euler scheme..."
        finalTime=times[-1]
        steps = int(finalTime/delta)
        t = self.startTime
        x=self.startPosition
        path=[]
        j=0
        time = times[j]
        for i in xrange(steps):
            if t+delta>time>t:
                delta = time-t
                x += self.drift(x,t)*delta + sqrt(delta)*self.diffusion(x,t)*self.Nor.rvs()
                path.append((x,time))
                delta=0.001
                j+=1
                time = times[j]
            else:
                x += self.drift(x,t)*delta + sqrt(delta)*self.diffusion(x,t)*self.Nor.rvs()
                t += delta
                path.append((x,time))

        return path    
    

class Wiener_process(Diffusion_process):
    """
    dW_t = mu*dt + sigma*dB_t
    
    parameters: 
    {mu: scalar, sigma: scalar>0}
    
    """
    

    def __init__(self, parameters, time_space_constraints):
        super(Wiener_process,self).__init__(time_space_constraints)
        for p in parameters:
            setattr(self,p,parameters[p])
        self.Nor = stats.norm()
    
    def _transition_pdf(self,x,t,y):
        return exp(-(y-x-self.mu*(t-self.startTime))**2/(2*self.sigma**2*(t-self.startTime)))\
            /sqrt(2*pi*self.sigma*(t-self.startTime))    
    
    def _get_mean_at(self,t):
        if self.conditional:
            delta1 = t - self.startTime
            delta2 = self.endTime - self.startTime
            return self.startPosition + self.mu*delta1 + (self.endPosition-self.startPosition-self.mu*delta2)*delta1/delta2
        else:
            return self.startPosition+self.mu*(t-self.startTime)

    def _get_variance_at(self,t):
        if self.conditional:
            delta1 = self.sigma**2*(t-self.startTime)*(self.endTime-t)
            delta2 = self.endTime-self.startTime
            return delta1/delta2
        else:
            return self.sigma**2*(t-self.startTime)
        
    def _generate_position_at(self,t):
            
            x= self.get_mean_at(t) + sqrt(self.get_variance_at(t))*self.Nor.rvs()
            return x
        
    def _generate_sample_path(self,times):
        t=self.startTime
        x=self.startPosition
        path=[]
        if not self.conditional:
            for time in times:
                delta = time - t
                x = x + self.mu*delta + self.sigma*math.sqrt(delta)*self.Nor.rvs()
                path.append((time,x))
                t = time
        else:
            T = self.endTime - self.startTime
            for time in times:
                delta = time - t
                x = x*(1-delta/T)+self.endPosition*delta/T + self.sigma*sqrt(delta/T*(T-delta))*self.Nor.rvs()
                T = T - delta
                t=time
                path.append((time,x))
        return path
    
    def generate_max(self,t):
        pass
    
    def generate_min(self,t):
        pass
    
    
    
    
class OU_process(Diffusion_process):
    
    """
    The Orstein-Uhlenbeck process
    
    dOU_t = theta*(mu-OU_t)*dt + sigma*dB_t
    
    parameters:
    {theta:scalar, mu:scalar, sigma:scalar>0}
    
    """
    def __init__(self, parameters, time_space_constraints):
        super(OU_process, self).__init__(time_space_constraints)
        for p in parameters:
            setattr(self, p, parameters[p])
        self.Normal = stats.norm()


    def _get_mean_at(self,t):
        def f(s):
            return self.startPosition*exp(-self.theta*(s-self.startTime))+self.mu*(1-exp(-self.theta*(s-self.startTime)))
        if self.conditional:
            pass
        else:
            return f(t)
                                                                
    def _get_variance_at(self,t):
        def v(s):
            return self.sigma**2*(1-exp(-2*self.theta*s))/(2*self.theta)
        if self.conditional:
            return super(OU_process,self)._get_variance_at(t)
        else:
            return v(t)
    
    def _transition_pdf(self,x,t,y):
        mu = x*exp(-self.theta*t)+self.mu*(1-exp(-self.theta*t))
        sigmaSq = self.sigma**2*(1-exp(-self.theta*2*t))/(2*self.theta)
        return exp(-(y-mu)**2/(2*sigmaSq))/sqrt(2*pi*sigmaSq)
        
    
    def _generate_position_at(self,t):
        if not self.conditional:
            return self.get_mean(t)+sqrt(self.get_variance(t))*self.Normal.rvs()
        else:
            pass
    
    def generate_sample_path(self,times, Normals = 0):
        "the parameter Normals = 0 is used for the Integrated OU Process"
        if not self.conditional:
            path = []
            listOfNormals = []
            t = self.startTime
            x = self.startPosition
            for time in times:
                delta = time - t
                mu = self.mu + exp(-self.theta*delta)*(x-self.mu)
                sigma = sqrt(self.sigma**2*(1-exp(-2*self.theta*delta))/(2*self.theta)) 
                N = self.Normal.rvs()
                x = mu + sigma*N
                listOfNormals.append(N)
                t = time
                path.append((t,x))
            if (Normals==0):
                return path
            else:
                return path, listOfNormals
        else:
            path = bridge_creation(self,times)
            return path
    
class Integrated_OU_process(Diffusion_process):
    """
    The time-integrated Orstein-Uhlenbeck process
    IOU_t = IOU_0 + \int_0^t OU_s ds
    where dOU_t = theta*(mu-OU_t)*dt + sigma*dB_t, 
    OU_0 = x0
    
    parameters:
    {theta:scalar, mu:scalar, sigma:scalar>0, x0:scalar}
    
    modified from http://www.fisica.uniud.it/~milotti/DidatticaTS/Segnali/Gillespie_1996.pdf
    """
    def __init__(self, parameters, time_space_constraints):
        super(Integrated_OU_process,self).__init__( time_space_constraints)
        self.OU = OU_process({"theta":parameters["theta"], "mu":parameters["mu"], "sigma":parameters["sigma"]}, {"startTime":time_space_constraints["startTime"], "startPosition":parameters["x0"]})
        for p in parameters:
            setattr(self, p, parameters[p])
        self.Normal = stats.norm()
        
    def _get_mean_at(self,t):
        delta = t - self.startTime
        if self.conditional:
            pass
        else:
            return self.startPosition + (self.x0-self.mu)/self.theta + self.mu*delta\
                            -(self.x0-self.mu)*exp(-self.theta*delta)/self.theta
    
    def _get_variance_at(self,t):
        delta = t - self.startTime
        if self.conditional:
            pass
        else:
            return self.sigma**2*(2*self.theta*delta-3+4*exp(-self.theta*delta)
                                  -2*exp(-2*self.theta*delta))/(2*self.sigma**3)


    def _generate_position_at(self,t):
        if self.conditional:
            pass 
        else:
            return self.get_mean(t)+sqrt(self.get_variance(t))*self.Normal.rvs()
    
    def _transition_pdf(self,x,t,y):
        mu = x + (self.x0 - self.mu)/self.theta + self.mu*t - (self.x0-self.mu)*exp(-self.theta*t)/self.theta
        sigmaSq = self.sigma**2*(2*self.theta*t-3+4*exp(-self.theta*t)-2*exp(-2*self.theta*t))/(2*self.sigma**3)
        return exp(-(y-mu)**2/(2*sigmaSq))/sqrt(2*pi*sigmaSq) 
    
        
    def generate_sample_path(self,times, returnUO = 0):
        "set returnUO to 1 to return the underlying UO path as well as the integrated UO path."
        if not self.conditional: 
            xPath, listOfNormals = self.OU.generate_sample_path(times, 1)
            path = []
            t = self.startTime
            y = self.startPosition
            for i, position in enumerate(xPath):
                delta = position[0]-t
                x = position[1]
                sigmaX = self.sigma**2*(1-exp(-2*self.theta*delta))/(2*self.theta)
                sigmaY = self.sigma**2*(2*self.theta*delta-3+4*exp(-self.theta*delta)
                                  -exp(-2*self.theta*delta))/(2*self.sigma**3)
                muY = y + (x-self.mu)/self.theta + self.mu*delta-(x-self.mu)*exp(-self.theta*delta)/self.theta
                covXY = self.sigma**2*(1+exp(-2*self.theta*delta)-2*exp(-self.theta*delta))/(2*self.theta**2)
                y = muY + sqrt(sigmaY - covXY**2/sigmaX)*self.Normal.rvs()+ covXY/sqrt(sigmaX)*listOfNormals[i]
                t = position[0]
                path.append((t,y))
                    
            if returnUO==0:
                return path
            else:
                return path, xPath
        else:
           path = bridge_creation(self,times)
           if returnUO==0:
               return path
           else:
               return path, xPath         
           
class SqBessel_process(Diffusion_process):
    """
    The (lambda0 dimensional) squared Bessel process is defined by the SDE:
                    dX_t = lambda0*dt + nu*sqrt(X_t)dW_t
        
    parameters:
    {lambda0:scalar, nu:scalar>0}
    or
    {mu:scalar} *see definition of mu below
    Attn: startPosition and endPosition>0
                    
                    
     Note that this process is strictly non-negative.
     An important parameter that determines the behaviour of the process near the boundary L=0 is 
     mu=2*lambda_0/nu^2 -1. L=0 is an entrance (it can leave the boundary but never return, i.e., enter its
     state space from L=0 but is reflecting there after) if mu>=0, regular if -1<mu<0, or exit if mu <=-1 
    (it may enter L=0, but is stuck there i.e. killed). Inputing the dictionary {mu:scalar}, one can parameterize
    the diffusion in this way. 
    
     Based on R.N. Makarov and D. Glew's research on simulating squared bessel process. See "Exact
     Simulation of Bessel Diffusions".
    """
    def __init__(self,parameters, time_space_constraints):
            super(SqBessel_process, self).__init__(time_space_constraints)
            self.x_0=4.0/parameters["nu"]**2*self.startPosition
            if parameters.has_key("mu"):
                self.mu = parameters["mu"]
            else:
                for p in parameters:
                    setattr(self, p, parameters[p])
                self.mu = 2*self.lambda0/(self.nu*self.nu)-1
            self.Poi = stats.poisson
            self.Gamma = stats.gamma
            self.InGamma = IncompleteGamma()
                
    
    def generate_sample_path(self,times,absb):
        """
        absb is a boolean, true if absorbtion at 0, false else. See class' __doc__ for when 
        absorption is valid.
        """
        if absb:
            return self._generate_sample_path_with_absorption(times)
        else:
            return self._generate_sample_path_no_absorption(times)
       
    
    def _transition_pdf(x,t,y):
        try:
            return (y/x)**(0.5*self.mu)*exp(-0.5*(x+y)/self.nu**2/t)/(0.5*self.nu**2*t)*iv(abs(self.mu),4*sqrt(x*y)/(self.nu**2*t))
        except AttributeError:
            print "Attn: nu must be known and defined to calculate the transition pdf."
            
    def _generate_sample_path_no_absorption(self, times):
        "mu must be greater than -1. The parameter times is a list of times to sample at."
        if self.mu<=-1:
            print "Attn: mu must be greater than -1. It is currently %f."%self.mu
            return
        else:
            if not self.conditional:
                x=self.x_0
                t=self.startTime
                path=[(t,x)]
                for time in times[1:]:
                    delta=time-t
                    y=self.Poi.rvs(0.5*x/delta)
                    x=self.Gamma.rvs(y+self.mu+1)*2*delta
                    path.append((time,x))
                    t=time
            else:
                path = bridge_creation(self, times,0)
            return [(p[0],self.rescalePath(p[1])) for p in path]
         
 
        
    def _generate_sample_path_with_absorption(self,times):
        "mu must be less than 0."
        if self.mu>=0:
            print "Attn: mu must be less than 0. It is currently %f."%self.mu
        else:
            if not self.conditional:
                path=[]
                X=self.x_0
                t=self.startTime
                tauEst=times[-1]+1
                for time in times:
                    delta = time - t
                    if tauEst>times[-1]:
                        p_a = gammaincc(abs(self.mu),0.5*X/(delta))
                        if random.random() < p_a:
                            tauEst = time
                    if time<tauEst:
                        Y = self.InGamma.rvs(abs(self.mu),0.5*X/(delta))
                        X = self.Gamma.rvs(Y+1)*2*delta
                    else:
                        X=0
                    t=time
                    path.append((t,X))
            else:
                path = bridge_creation(self, times, 1)
            return  [(p[0],self.rescalePath(p[1])) for p in path]
                    

    def _generate_position_at(self,t):
        pass
    
    
    def generate_sample_FHT_bridge(self,times):
        "mu must be less than 0. This process has absorption at L=0. It simulates the absorption at 0 at some random time, tao, and creates a bridge process."
        if self.mu>0:
            print "mu must be less than 0. It is currently %f."%self.mu
        else:
            X=self.x_0
            t=self.t_0
            path=[]
            FHT=self.x_0/(2*self.Gamma.rvs(abs(self.mu)))
            for time in times:
                if time<FHT:
                    d=(FHT-t)*(time-t)
                    Y=self.Poi.rvs(X*(FHT-time)/(2*d))
                    X=self.Gamma.rvs(Y-self.mu+1)*d/(FHT-t)
                else:
                    X=0
                t=time
                path.append((t,X))
            return  [(p[0],self.rescalePath(p[1])) for p in path]
    
    
    def rescalePath(self,x):
        #All of the simulation algorithms assume nu=2, so we must
        # rescale the process to output a path that is has the user specified
        # nu. Note that this rescaling does not change mu.
        return self.nu**2/4.0*x
    
    
class CIR_process(Diffusion_process):
    """
    The CIR process is defined by
    dCIR_t = (lambda_0 - lambda_1*CIR_t)dt + nu*sqrt(CIR_t)*dB_t
    
    This is a mean reverting process if both lambdas are positive: the process flucuates around lambda_0/lambda_1
    
    parameters:
    {lambda_0:scalar, lambda_1:scalar, nu:scalar>0}
    
    """
    def __init__(self, parameters, space_time_constraints):
        super(CIR_process,self).__init__(space_time_constraints)
        for p in parameters:
            setattr(self, p, parameters[p])
        self.Normal = stats.norm()
        self.SqB = SqBessel_process({"lambda0":parameters["lambda_0"], "nu":parameters["nu"]}, space_time_constraints) #need to change start position for non-zero startTime
        self.mu=self.SqB.mu
    
    
    def _transition_pdf(self,x,t,y):
        return exp(self.lambda_1*t)*SqB._transition_pdf(x,self._time_transformation(t), exp(self.lambda_1*t)*y)
    
    def generate_sample_path(self, times, abs):
        "abs is a boolean: true if desire nonzero probability of absorption at 0, false else."
        #first, transform times:
        transformedTimes = [self._time_transformation(t) for t in times]
        path = self.SqB.generate_sample_path(transformedTimes,abs)
        tpath = [self._space_transformation(times[i],p[1]) for i,p in enumerate(path) ]
        path=[]
        for i in range(len(tpath)):
            path.append((times[i],tpath[i]))
        return path
    
    def _time_transformation(self,t):
        if self.lambda_1==0:
            return t
        else:
            return (exp(self.lambda_1*t)-1)/self.lambda_1
        
    def _space_transformation(self,t,x):
        return exp(-self.lambda_1*t)*x
    
    def _get_mean_at(self,t):
        pass
    
    def _get_variance_at(self,t):
        pass

class CEV_process(Diffusion_process):
    """
    defined by:
    dCEV = r*CEV*dt + delta*CEV^{beta+1}*dW_t
    
    parameters:
    {r: scalar, delta:scalar>0, beta:scalar<0} #typically beta<=-1/2
    
    """
    
    def __init__(self,parameters, time_space_constraints):
        super(CEV_process,self).__init__(time_space_constraints)
        for p in parameters:
            setattr(self, p, parameters[p])
        time_space_constraints["startPosition"]=self.CEV_to_SqB(self.startPosition)
        self.SqB = SqBessel_process({"lambda0":(2-1/self.beta), "nu":2}, time_space_constraints)
        
    def _time_transform(self,t):
        if self.r*self.beta==0:
            return t
        else:
            return (exp(self.r*self.beta*2*t)-1)/(self.r*self.beta*2)
        
    def CEV_to_SqB(self,x):
        return x**(-2*self.beta)/(self.delta*self.beta)**2
    
    def _scalar_space_transform(self,t,x):
        return exp(self.r*t)*x
    
    def SqB_to_CEV(self,x):
        ans = (self.delta**2*self.beta**2*x)**(-1/(2.0*self.beta))
        return ans
    
#    def _get_mean_at(self,t):
#       pass
    
#    def _get_variance_at(self,t):
#        pass
    
    def generate_sample_path(self,times, abs):
        if self.r==0:
            SqBPath = self.SqB.generate_sample_path(times, abs)
            return [(x[0],self.SqB_to_CEV(x[1])) for x in SqBPath]
        else:
            transformedTimes = [self._time_transform(t) for t in times]
            SqBPath = self.SqB.generate_sample_path(transformedTimes, abs)
            tempPath = [self.SqB_to_CEV(x[1]) for x in SqBPath]
            return [(times[i], self._scalar_space_transform(times[i], p) ) for i,p in enumerate(tempPath)]
        
    def _generate_position_at(self,t):
        #still need to create the Sqb _generate_position_at(t) method
        if self.r==0:
            SqBpos = self.SqB.generate_position_at(t)
            return self.SqB_to_CEV(SqBpos)
        else:
            transformedTime = self._time_transform(t)
            SqBpos = self.SqB.generate_position_at(transformedTime)
            return self.SqB_to_CEV(SqBpos)
        
        
class Periodic_drift_process(Diffusion_process):
    """
      dX_t = psi*sin(X_t + theta)dt + dBt 
      
      parameters:
      {psi:scalar>0, theta:scalar>0}
      
      
      This cannot be conditioned on start or end conditions.
      Extensions to come. 
    """
    def __init__(self, parameters):
        space_time_constraints = {"startTime":0, "startPosition":0}
        super(Periodic_drift_process,self).__init__(space_time_constraints)
        self.psi = parameters["psi"]
        self.theta = parameters["theta"]
        self._findBounds()        
        self.BB = Wiener_process({"mu":0, "sigma":1}, space_time_constraints) #brownian bridge
        self.BB.conditional = True
        self.Poi = Marked_poisson_process({"rate":1, "U":self.max, "L":self.min, "startTime":0})
        self.Nor = stats.norm
        self.Uni = stats.uniform()

    def append_sample_path(self,T):
        "currently will only return a random path before time T. Can be connected by brownian bridges"

        time = 0
        endPoint = 0
        skeleton=[]
        
        while time<T:
            if time+2<T:
                delta=2
            else:
                delta = T-time
            endPoint, tempSkeleton = self._generate_sample_path(delta,endPoint)
            tk = [(time + x[0],x[1]) for x in tempSkeleton] 
            skeleton+=tk
            
            time+=2
        
    
        return [(0,self.startPosition)]+skeleton

    def generate_sample_path(self,times):
        # this algorithm uses the EA1 algorithm by Beskos and 
        # Roberts on exact simulation of diffusions. It's an AR algorithm.
        # For some parameters, the probability of acceptance can be very low.
        randomPath = self.append_sample_path(times[-1]) #this returns [(0,0), (tao_1, W_tao_1), ...,(times[-1],W_times[-1])]
        path=[]
        count=0
        self.__set_Bridge_parameters(randomPath[count],randomPath[count+1])
        tao = randomPath[count+1][0]
        for time in times:
            if time<tao:
                x=self.BB.generate_position_at(time)
                path.append((time,x))
                self.BB.startTime=time
                self.BB.startPosition=x

            else:
                while time>tao: #iterate until we find the next tao.
                    count+=1
                    tao = randomPath[count+1][0]

                self.__set_Bridge_parameters(randomPath[count],randomPath[count+1])
                                
                x=self.BB.generate_position_at(time)
                path.append((time,x))
                self.BB.startTime=time
                self.BB.startPosition=x
        return path
                
        
    def __set_Bridge_parameters(self, startPoint, endPoint):
        self.BB.startTime = startPoint[0]
        self.BB.startPosition = startPoint[1]
        self.BB.endTime = endPoint[0]
        self.BB.endPosition = endPoint[1]
                    
        
    def _generate_sample_path(self,T,x):
        #generates a path of length 2. This is for efficiency issues
        self.BB.startPosition=x
        while (True):
            
            
            #produce a marked poisson process
            markedProcess = self.Poi.generate_marked_process(T)

            #generate end point using an AR scheme
            while (True):
                N = x+ sqrt(T)*self.Nor.rvs()
                U = self.Uni.rvs()
                if U<=exp(-self.psi*cos(N-self.theta)+self.psi):
                    break
            self.BB.endPosition = N
            self.BB.endTime = T
        
            #generate brownian bridge
            skeleton = self.BB.generate_sample_path([p[0] for p in markedProcess])
            transformSkeleton = [self.phi(p[1]) for p in skeleton[1:]]
            
            #calculate indicators
            I=1
            for i in range(len(transformSkeleton)):
                if transformSkeleton[i]>markedProcess[i][1]:
                    I=0
                    break
            
            #check indicators
            if I==1:
                return N, skeleton + [(T,N)]
                
    
    def _findBounds(self):
        if self.psi<=.5:
            self.max = self.psi
        else:
            self.max = 0.125+0.5*(self.psi*self.psi+self.psi)
        self.min = -self.psi*.5
    
    def phi(self,x):
        return (0.5*self.psi*self.psi*sin(x-self.theta)**2+0.5*self.psi*cos(x-self.theta)-self.min)/self.max

class GBM_process(Diffusion_process):
    """The Geometric Brownian Motion process defined by
    dGBM_t = mu*GBM_t*dt + sigma*GBM_t*dW_t
    and has general solution GBM_t = GBM_0*exp{ (mu - 0.5sigma**2)*t + sigma*W_t)
    
    parameters:
    { mu:scalar, sigma:scalar>0}
    
    """
    
    def __init__(self, parameters, t_s_c):
        super(GBM_process,self).__init__(t_s_c)
        self.mu = parameters["mu"]
        self.sigma = parameters["sigma"]
        self.Nor = stats.norm(0,1)
        try:
            wienerConstraints = {"startTime":self.startTime, "endTime":self.endTime, "startPosition":0, "endPosition":log(self.endPosition/self.startPosition)}
        except:
            wienerConstraints = {"startTime":self.startTime, "startPosition":0}
        self.Weiner = Wiener_process({"mu":(self.mu-0.5*self.sigma**2), "sigma":self.sigma}, wienerConstraints)
        
    def _get_mean_at(self,t):
        if not self.conditional:
            return self.startPosition*exp(self.mu*t)
        else:
           delta = self.endPosition - self.startPosition
           return self.startPosition*exp(-0.5*(self.sigma*t)**2/delta+self.Weiner.endPosition*t/delta)        
            
    def _transition_pdf(self,x,t,y):
        delta = t - self.startTimee
        d = (self.mu - 0.5*self.sigma**2)
        return  x/(y*sqrt(2*Pi*self.sigma**2**delta))*exp(-(log(y/x)-d)**2/(2*self.sigma**2*delta))
    
    def _get_variance_at(self,t):
        if not self.conditonal:
            return self.startPosition**2*exp(2*self.mu*t)*(exp(self.sigma**2*t)-1)
        else:
            X=log(self.endPosition/self.startPosition)-(self.mu-0.5*(self.sigma**2))*T
            X=X/self.sigma
            delta = self.endTime-self.startTime
            return self.startPosition**2*exp(2*self.mu*t-self.sigma**2*t + self.sigma*t/delta*(self.sigma*(delta-T)+2*X))*(exp(self.sigma**2*(delta-t)*t/delta)-1)
        
    def _generate_position_at(self,t):
        return self.startPosition*exp((self.mu-0.5*self.sigma**2)*(t-self.startTime) + self.sigma*sqrt(t-self.startTime)*self.Nor.rvs() )
        
    def _generate_sample_path(self,times):
        return [(p[0],self.startPosition*exp(p[1])) for p in self.Weiner.generate_sample_path(times)]
        
    
    
class Custom_diffusion(Diffusion_process):
    """
    simulates the diffusion:
    dX_t = a(X_t,t)*dt + b(X_t,t)*dW_t
    
    where a and b are inputed functions
    
    parameters:
    {a:time and space function, b:nonnegative time and space function}
    Ex:
    def f1(x,t):
        return x^2-t
        
    def f2(x,t):
        return sqrt(x)
    param = {"a":f1, "b":f2}
    
    
    
    The superclass Diffusion_process contains most of the methods for this class. See it's documentation for all.
    """
    def __init__(self,parameters,space_time_constraints):
        super(Custom_diffusion, self).__init__(space_time_constraints)
        self.drift = parameters["a"]
        self.diffusion = parameters["b"]
    
    
    
    

class Jump_Diffusion_process(object):
    
    def __init__(self,dict):    
        try:
            self.startTime = dict["startTime"]
            self.startPosition = dict["startPosition"]
            self.conditional=False
            if dict.has_key("endTime"):
                self.endTime = dict["endTime"]
                self.endPosition = dict["endPosition"]
                self.conditional=True
        except KeyError:
            print "Missing constraint in initial\end value dictionary. Check spelling?"    
    def transition_pdf(self,t,y):
        "this method calls self._transition_pdf(x) in the subclass"
        self._check_time(t)
        if not self.conditional:
            return self._transition_pdf(self.startPosition, t-self.startTime, y)
        else:
            return self._transition_pdf(self.startPosition, t-self.startTime, y)*self._transition_pdf(y, self.endTime-t, self.endPosition)\
                    /self._transition_pdf(self.startPosition,self.endTime - self.startTime, self.endPosition)
    

    def expected_value(self,f,t,N):
        "uses a monte carlo approach to evaluate the expected value of the process f(X_t). N is the number of iterations. The parameter f\
        is a univariate python function."
        print "Attn: performing a Monte Carlo simulation..."
        self._check_time(t)
        if not self.conditional:
            sum=0
            for i in range(N):
                sum+=f(self.generate_position_at(t))
            return sum/N
        else:
            #This uses a change of measure technique.
            sum=0
            self.conditional=False
            for i in range(N):
                X = self.generate_position_at(t)
                sum+=self._transition_pdf(X,self.endTime-t,self.endPosition)*f(X)
            self.conditional=True
            return sum/(N*self._transition_pdf(self.startPosition, self.endTime-self.startTime, self.endPosition))
        
    def generate_position_at(self,t):
        "if _get_position_at() is not overwritten in a subclass, this function will use euler scheme"
        self._check_time(t)        
        if self.startTime<t:
            return self._generate_position_at(t)
        
    
    def get_mean_at(self,t):
        self._check_time(t)
        return self._get_mean_at(t)
    
    
    def get_variance_at(self,t):
        self._check_time(t)
        return self._get_variance_at(t)
    
    def generate_sample_path(self,times):
        '"times" is a list of times, with the first time greater than initial time."'
        self._check_time(times[0])
        return self._generate_sample_path(times)
    
    
    def _generate_sample_path(self,times):
        "I need some way to use a euler scheme AND evaluate the approximation at t in times"
        pass
    
    def _get_variance_at(self,t):
        var = SampleVarStat()
        for i in range(10000):
            var.push(self.generate_position_at(t))
        return var.get_variance()
    
    
    def _get_mean_at(self,t):
        "if _get_mean_at() is not overwritten, then we use MC methods; 100000 iterations"
        def id(x):
            return x
        return self.expected_value(id, t, 100000)
    
    def _generate_position_at(self,T,delta=0.001):
        return self.Euler_scheme(t,return_array=False)
        
    def _transition_pdf(self,x,t,y):
        print "Attn: transition pdf not defined"

    def _check_time(self,t):
        if t<self.startTime:
            print "Attn: inputed time not valid (check if beginning time is less than startTime)."
    
        

class Gamma_process(Jump_Diffusion_process):
    """
    Defined by G(t+h) - G(t) is distributed as a Gamma random variable. 
    parameters:
    {"mean":scalar>0, "variance":scalar>0}
    or
    {"rate":scalar>0, "size":scalar>0}
    
    
    Under the first parameterization: E[G(t)] = mean*t, Var(G(t)) = variance*t
    Under the second parameterization: G(t+1) - G(t) ~ Gamma(rate, size)
    where Gamma has pdf [size^(-rate)/gamma(rate)]*x^(rate-1)*exp(-x/size)
    
    see http://eprints.soton.ac.uk/55793/1/wsc03vg.pdf for details on this process.
    
    """
    
    def __init__(self, parameters, time_space_constraints):
        super(Gamma_process,self).__init__(time_space_constraints)
        try:
            self.mean = parameters["rate"]/parameters["size"]
            self.variance = self.mean/parameters["size"]
        except KeyError:
            self.mean = parameters["mean"]
            self.variance = parameters["variance"]
        self.gamma = stats.gamma
        self.beta = stats.beta
        
    def _generate_position_at(self,t):
        if not self.conditional:
            return self.x + self.gamma.rvs(self.mean**2*(T-self.startTime)/self.variance)*self.mean/self.variance
        else:
            return self.startPosition + (self.endPosition-self.startPosition)*self.beta.rvs((t-self.startTime)/self.variance, (self.endTime-t)/self.variance)
            
    def _get_mean_at(self,t):
        "notice the conditional is independent of self.mean."
        if self.conditional:
            return self.startPosition + (self.endPosition-self.startPosition)*(t- self.startTime)/(self.endTime - self.startTime)
        else:
            return self.x + self.mean*(t-self.startTime)
    
    def _get_variance_at(self,t):
        if self.conditional:
            alpha = (t-self.startTime)/self.variance
            beta = (self.endTime-t)/self.variance
            return (self.endPosition-self.startPosition)**2(alpha*beta)/(alpha+beta)**2/(alpha+beta+1)
        else:
            return self.variance*(t-self.startTime)
    
        
    def _generate_sample_path(self,times):
        if not self.conditional:
            t = self.startTime
            x = self.startPosition
            path=[]
            for time in times:
                delta = time - t
                g = self.gamma.rvs(self.mean**2*delta/self.variance)*self.variance/self.mean
                x = x + g
                t = time
                path.append((t,x))
            return path
        else:
            x = self.startPosition
            t = self.startTime
            path=[]
            for time in times:
                delta1 = time -t
                delta2 = self.endTime - time
                x = x + (self.endPosition-x)*self.beta.rvs(delta1/self.variance,delta2/self.variance)
                t = time
                path.append((t,x))
            return path
    
    def _transition_pdf(self,x,t,y):
        return self.variance/self.mean*self.gamma.pdf((y-x)*self.mean/self.variance*t,self.mean**2/self.variance)
    
    
class Gamma_variance_process(Jump_Diffusion_process):
    """
    The Gamma variance process is a brownian motion subordinator:
    VG_t = mu*G_t(t,a,b) + sigma*B_{G_t(t,a,b)}
    i.e. VG process is a time transformed brownian motion plus a scalar drift term.
    It can also be represented by the difference of two gamma processes. 
    
    Note: currently, if conditional, endPosition=0. Further extensions will be to make this nonzero.
    
    parameters:
    {mu:scalar, sigma:scalar>0, variance:scalar>0} 
    or
    {mu:scalar, sigma:scalar>0, rate:scalar>0}
    *note the mean of the gamma process is 1, hence the reduction of parameters needed.
    
    The parameterization depends on the way you parameterize the underlying gamma process.   
    See http://www.math.nyu.edu/research/carrp/papers/pdf/VGEFRpub.pdf"
    """
    
    def __init__(self,parameters, space_time_constraints):
        super(Gamma_variance_process,self).__init__(space_time_constraints)
        try:
            self.variance=v = parameters["variance"]
        except KeyError:
            self.variance=v = 1/parameters["rate"]
        self.sigma=s = parameters["sigma"]
        self.mu=m = parameters["mu"]
        self.mu1 = 0.5*sqrt(m**2 + 2*s**2/v)+m/2
        self.mu2 = 0.5*sqrt(m**2 + 2*s**2/v)-m/2
        self.var1 = self.mu1**2*v
        self.var2 = self.mu2**2*v
        self.GamPos = Gamma_process({"mean":self.mu1,"variance":self.var1}, space_time_constraints)
        self.GamNeg = Gamma_process({"mean":self.mu2, "variance":self.var2}, space_time_constraints)
        
        
    def _get_mean_at(self,t):
        return self.GamPos.get_mean_at(t)-self.GamNeg.get_mean_at(t)
    
    def _get_variance_at(self,t):
        return self.GamPos.get_variance_at(t)+self.GamNeg.get_variance_at(t)
        
    def _generate_position_at(self,t):
        return self.GamPos.generate_position_at(t)-self.GamNeg.generate_position_at(t)

    def _generate_sample_path(self,times):
        path=[]
        pathPos = self.GamPos.generate_sample_path(times)
        pathNeg = self.GamNeg.generate_sample_path(times)
        for i,time in enumerate(times):
            path.append((time, pathPos[i][1] - pathNeg[i][1]))
        return path
    
    def _transition_pdf(self,x,t,y):
        alpha1=self.mu1**2*t/self.var1
        beta1 = self.var1/self.mu2
        alpha2 = self.mu2**2*t/self.var2
        beta2 = self.var2/self.mu2
        return exp(-(y-x))
    
    
class Geometric_gamma_process(Jump_Diffusion_process):
        """
        the geometric gamma process has the representation GG_0*exp(G_t) where G_t is a gamma process.
        
        parameters
        {mu: scalar, sigma: scalar>0 } 
        The parameters refer to the parameters in the gamma process (mu = mean, sigma = variance) (see gamma_process documentation for more details).
    
        """
        
        def __init__(self, parameters, space_time_constraints):
            super(Geometric_gamma_process, self).__init__(space_time_constraints)
            self.mu = parameters["mu"]
            self.sigma = parameters["sigma"]
            try:
                self.gammaProcess = Gamma_process({"mean":self.mu, "variance":self.sigma}, {"startPosition":0, "startTime":0, "endTime":self.endTime, "endPosition":log(self.endPosition/self.startPosition)})
            except:
                self.gammaProcess = Gamma_process({"mean":self.mu, "variance":self.sigma}, {"startPosition":0, "startTime":0})

        
        
        def _transition_pdf(self,z,t,x):
            "as this is a strictly inceasing process, the condition x<z must hold"
            alpha = self.mu**2*t/self.sigma
            beta = self.sigma/self.mu
            return (log((z-x)/self.startPosition))**(alpha-1)*((z-x)/self.startPosition)**(-1/beta)/((z-x)*beta**alpha*gamma(alpha))
        
        def _get_mean_at(self,t):
            if self.conditional:
                pass
            else:
                if self.sigma<self.mu: #this condition gauruntees the expectation exists
                    return self.startPosition*(1-self.sigma/self.mu)**(-self.mu**2*(t-self.startTime)/self.sigma)
                else:
                    print "Attn: does not exist."
        
        def _generate_sample_path(self,times):
            return [(p[0],self.startPosition*exp(p[1])) for p in self.gammaProcess.generate_sample_path(times)]
        
        def _generate_position_at(self,t):
            return exp(self.gammaProcess.generate_position_at(t))
        
        
        
            

class Custom_process:
    """
    This class is a user defined sum of processes. The parameters are classes from this module.    
    Ex: 
    WP = Wiener_process{parametersWP, spaceTimeConstraintsWP}
    PP = Poisson_process{parametersPP, space_time_constraintsPP}
    Custom = Custom_process( WP, PP )
    
    Custom.get_mean_at(10)
    
    
    """
    def __init__(self, *args):
        self.processes = []
        for arg in args:
            self.processes.append(arg)
        
    def get_mean_at(self,t):
        sum=0
        for p in self.processes:
            sum+=p.get_mean_at(t)
        return sum
    
    def get_variance_at(self,t):
        sum=0
        for p in self.processes:
            sum+=p.get_variance_at(t)
        return sum

    def generate_position_at(self,t):
        sum=0
        for p in self.processes:
            sum+=p.generate_position_at(t)
        return sum
    
    def generate_sample_path(self,times, *args):
        "returns an array of a path, not an immutable list!"
        path = [[t,0] for t in times]
        for i in range(len(self.processes)):
            try:
              tempPath = self.processes[i].generate_sample_path(times, args[i] )
            except:
              tempPath = self.processes[i].generate_sample_path(times)
            for k in xrange(len(tempPath)):
                path[k][1]+=tempPath[k][1]
        return path
    
    
    
    
            
            
#------------------------------------------------------------------------------ 
# auxilary classes and functions

class Constant:
    def __init__(self,c):
        self.c=c
        
    def mean(self):
        return self.c
    def var(self):
        return 0
    def rvs(self):
        return self.c
    def cdf(self,x):
        if x<self.c:
            return 0
        else:
            return 1
    def sf(self,x):
        return 1-self.cdf(x)
    
    def pmf(self,x):
        if x==self.c:
            return 1
        else:
            return 0



def bridge_creation(process,times, *args):
   # this algorithm relies on the fact that 1-dim diffusion are time reversible.
    print "Attn: using an AR method..."
    process.conditional = False
    temp = process.startPosition
    while (True):
        sample_path=[]
        forward = process.generate_sample_path(times, *args)
        process.startPosition = process.endPosition
        backward = process.generate_sample_path(reverse_times(process, times), *args)
        process.startPosition = temp
        check = (forward[0][1]-backward[-1][1]>0)
        i=1
        N = len(times)
        sample_path.append(forward[0])
        while (check == (forward[i][1]-backward[-1-i][1]>0) and i<N-1):
            sample_path.append(forward[i])
            i+=1
        
        if i != N-1: #an intersection was found
            k=0
            while(N-1-i-k>=0):
                sample_path.append((times[i+k],backward[N-1-i-k][1]))
                k+=1
            process.conditional = True

            return sample_path
                
        
    
def reverse_times(process, times):
    reverse_times=[]
    for time in reversed(times):
        reverse_times.append(process.endTime - time - process.startTime)
    return reverse_times

def transform_path(path,f):
    "accepts a path, ie [(t,x_t)], and transforms it into [(t,f(x)]."
    return [(p[0],f(p[1])) for p in path]

class SampleVarStat:
    def __init__(self):
        self.S=0
        self.oldM=0
        self.newM=0
        self.k=1
        
        
    
    def push(self,x):
        if self.k==0:
            self.S=0
            self.oldM=x
        else:
            self.newM = self.oldM+(x-self.oldM)/self.k
            self.S+=(x-self.oldM)*(x-self.newM)
            self.oldM=self.newM
            
        self.k+=1
    
    def get_variance(self):
        return self.S/(self.k-1)
    
class IncompleteGamma:
    "defined on negative integers. This is untested for accuracy"
    "Used in Bessel process simulation."
    def __init__(self,shape=None,scale=None):
        self.shape = shape
        self.scale = scale
        self.Uni = stats.uniform
        
    def pdf(self,n,shape,scale):
        inc = gammainc(shape,scale) #incomplete gamma function
        return math.exp(-scale)*math.pow(scale, n+shape)/(gamma(n+1+shape)*inc)
    
    def cdf(self,n, shape,scale):
        sum=0
        for i in range(n+1):
            sum+=self.pdf(i,shape,scale)
        return sum
    
    def rvs(self,shape,scale):
        "uses a inversion method: the chop-down-search starting \
        at the mode"
        pos =  mode = float(max(0,int(shape-scale)))
        U = self.Uni.rvs()
        sum = self.pdf(mode,shape,scale)
        ub = mode+1
        lb = mode-1
        Pub = sum*scale/(mode+1+shape)
        Plb = sum*(mode+shape)/scale
        while sum<U:
            if Plb>Pub and lb>=0:
                sum+=Plb
                pos = lb
                Plb = (lb+shape)/scale*Plb
                lb-=1
            else:
                sum+=Pub
                pos= ub
                Pub = scale/(ub+1+shape)*Pub
                ub+=1
        return float(pos)
    
    def rvsII(self,shape,scale):
        U = self.Uni.rvs()
        pos = 0
        sum = self.pdf(pos,shape,scale)
        while sum<U:
            pos+=1
            sum+=self.pdf(pos,shape,scale)
        return float(pos)
