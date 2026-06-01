Optimal Brain Damage

Yann Le Cun, John S. Denker and Sara A. Solla AT&T Bell Laboratories, Holmdel, N. J. 07733

ABSTRACT

We have used information-theoretic ideas to derive a class of practical and nearly optimal schemes for adapting the size of a neural network. By removing unimportant weights from a network, several improvements can be expected: better generalization, fewer training examples required, and improved speed of learning and/or classification. The basic idea is to use second-derivative information to make a tradeoff between network complexity and training set error. Experiments confirm the usefulness of the methods on a real-world application.

1 INTRODUCTION

Most successful applications of neural network learning to real-world problems have been achieved using highly structured networks of rather large size \[for example (Waibel, 1989; Le Cun et al., 1990a)\]. As applications become more complex, the networks will presumably become even larger and more structured. Design tools and techniques for comparing different architectures and minimizing the network size will be needed. More importantly, as the number of parameters in the systems increases, overfitting problems may arise, with devastating effects on the generalization performance. We introduce a new technique called Optimal Brain Damage (OBD) for reducing the size of a learning network by selectively deleting weights. We show that OBD can be used both as an automatic network minimization procedure and as an interactive tool to suggest better architectures.

* * *

be solved, and the system must make optimal use of a limited amount of training data. It is known from theory (Denker et al., 1987; Baum and Haussler, 1989; Solla et al., 1990) and experience (Le Cun, 1989) that, for a fixed amount of training data, networks with too many weights do not generalize well. On the other hand. networks with too few weights will not have enough power to represent the data accurately. The best generalization is obtained by trading off the training error and the network complexity.

One technique to reach this tradeoff is to minimize a cost function composed of two terms: the ordinary training error, plus some measure of the network complexity. Several such schemes have been proposed in the statistical inference literature \[see (Akaike, 1986; Rissanen, 1989; Vapnik, 1989) and references therein\] as well as in the NN literature (Rumelhart, 1988; Chauvin, 1989; Hanson and Pratt, 1989; Mozer and Smolensky, 1989).

Various complexity measures have been dimensionality (Vapnik and Chervonenkis 1989). A time-honored (albeit inexact) me of non-zero free parameters, which is the \[but see (Denker, Le Cun and Solla, 1990) connections, since in constrained networks a single parameter.\
\
opposed, including Vapnik-Chervonenkis (1971) and description length (Rissanen, sure of complexity is simply the number measure we choose to use in this paper Free parameters are used rather than several connections can be controlled by\
\
In most cases in the statistical inference literature, there is some a priori or heuristic information that dictates the order in which parameters should be deleted; for example, in a family of polynomials, a smoothness heuristic may require high-order terms to be deleted first. In a neural network, however, it is not at all obvious in which order the parameters should be deleted.\
\
A simple strategy consists in deleting parameters with small "saliency", i.e. those whose deletion will have the least effect on the training error. Other things being equal, small-magnitude parameters will have the least saliency, so a reasonable initial strategy is to train the network and delete small-magnitude parameters in order. After deletion, the network should be retrained. Of course this procedure can be iterated; in the limit it reduces to continuous weight-decay during training (using disproportionately rapid decay of small-magnitude parameters). In fact, several network minimization schemes have been implemented using non-proportional weight decay (Rumelhart, 1988; Chauvin, 1989; Hanson and Pratt, 1989), or "gating coefficients" (Mozer and Smolensky, 1989). Generalization performance has been reported to increase significantly on the somewhat small problems examined. Two drawbacks of these techniques are that they require fine-tuning of the "pruning" coefficients to avoid catastrophic effects, and also that the learning process is significantly slowed down. Such methods include the implicit hypothesis that the appropriate\
\
One of the main points of this paper is to move beyond the approximation that "magnitude equals saliency", and propose a theoretically justified saliency measure.\
\
* * *\
\
Our technique uses the second derivative of the objective function with respect to the parameters to compute the saliencies. The method was validated using our handwritten digit recognition network trained with backpropagation (Le Cun et al., 1990b).\
\
2 OPTIMAL BRAIN DAMAGE\
\
Objective functions play a central role in this field; therefore it is more than reasonable to define the saliency of a parameter to be the change in the objective function caused by deleting that parameter. It would be prohibitively laborious to evaluate the saliency directly from this definition, i.e. by temporarily deleting each parameter and reevaluating the objective function.\
\
Fortunately, it is possible to construct a local model of the error function and analytically predict the effect of perturbing the parameter vector. We approximate the objective function E by a Taylor series. A perturbation $ \\mathcal{E} $ of the parameter vector will change the objective function by\
\
$$\
\\mathrm {a c}\
$$\
\
$$\
\\delta E = \\sum\_ {i} g \_ {i} \\delta u \_ {i} + \\frac {1}{2} \\sum\_ {i} h \_ {i i} \\delta u \_ {i} ^ {2} + \\frac {1}{2} \\sum\_ {i \\neq j} h \_ {i j} \\delta u \_ {i} \\delta u \_ {j} + O \\left(\| \\delta^ {-} \| ^ {3}\\right)\
$$\
\
(1)\
\
Here, the $ \\delta u\_{i} $ 's are the components of $ \\delta U $ , the $ g\_{i} $ 's are the components of the gradient G of E with respect to U, and the $ h\_{ij} $ 's are the elements of the Hessian matrix H of E with respect to U:\
\
$$\
\\delta u \_ {i}\
$$\
\
$$\
8 U\
$$\
\
$$\
g \_ {i} ^ {\\prime}\
$$\
\
$$\
G\
$$\
\
$$\
h \_ {i j}\
$$\
\
$$\
U\
$$\
\
$$\
g \_ {i} = \\frac {\\partial E}{\\partial u \_ {i}} \\quad \\text {a n d} \\quad h \_ {i j} = \\frac {\\partial^ {2} E}{\\partial u \_ {i} \\partial u \_ {j}}\
$$\
\
(2)\
\
The goal is to find a set of parameters whose deletion will cause the least increase of $ E $ . This problem is practically insoluble in the general case. One reason is that the matrix $ H $ is enormous $( 6.5 \\times10^{6} $ terms for our 2600 parameter network), and is very difficult to compute. Therefore we must introduce some simplifying approximations. The "diagonal" approximation assumes that the $ \\delta E $ caused by deleting several parameters is the sum of the $ \\delta E $ 's caused by deleting each parameter individually; cross terms are neglected, so third term of the right hand side of equation 1 is discarded. The "extremal" approximation assumes that parameter deletion will be performed after training has converged. The parameter vector is then at a (local) minimum of $ E $ and the first term of the right hand side of equation 1 can be neglected. Furthermore, at a local minimum, all the $ h\_{ii} $ 's are non-negative, so any perturbation of the parameters will cause $ E $ to increase or stay the same. Thirdly, the "quadratic" approximation assumes\
\
$$\
h \_ {i i} ^ {\\prime s}\
$$\
\
$$\
\\delta E = \\frac {1}{2} \\sum\_ {i} h \_ {i i} \\delta u \_ {i} ^ {2}\
$$\
\
* * *\
\
2.1 COMPUTING THE SECOND DERIVATIVES\
\
Now we need an efficient way of computing the diagonal second derivatives $ h\_{ii} $ Such a procedure was derived in (Le Cun, 1987), and was the basis of a fast backpropagation method used extensively in various applications (Becker and Le Cun, 1989; Le Cun, 1989; Le Cun et al., 1990a). The procedure is very similar to the back-propagation algorithm used for computing the first derivatives. We will only outline the procedure; details can be found in the references.\
\
$$\
h \_ {i i}\
$$\
\
We assume the objective function is the usual mean-squared error (MSE); generalization to other additive error measures is straightforward. The following expressions apply to a single input pattern; afterward E and H must be averaged over the training set. The network state is computed using the standard formulae\
\
(4)\
\
$$\
x \_ {i} = f \\left(a \_ {i}\\right) \\quad \\text {a n d} \\quad a \_ {i} = \\sum\_ {j} w \_ {i j} x \_ {j}\
$$\
\
where $ x\_{i} $ is the state of unit i, $ a\_{i} $ its total input (weighted sum), f the squashing function and $ w\_{ij} $ is the connection going from unit j to unit i. In a shared-weight network like ours, a single parameter $ u\_{k} $ can control one or more connections: $ w\_{ij}= $ $ u\_{k} $ for all $( i,j)\\in V\_{k} $ , where $ V\_{k} $ is a set of index pairs. By the chain rule, the diagonal terms of H are given by\
\
$$\
i, a \_ {i}\
$$\
\
$$\
x \_ {i}\
$$\
\
$$\
w \_ {i j}\
$$\
\
$$\
j\
$$\
\
$$\
w \_ {i j} =\
$$\
\
$$\
u k\
$$\
\
$$\
(i, j) \\in V \_ {k}\
$$\
\
$$\
V \_ {k}\
$$\
\
$$\
h \_ {k k} = \\sum\_ {(i, j) \\in V \_ {k}} \\frac {\\partial^ {2} E}{\\partial w \_ {i j} ^ {2}}\
$$\
\
(5)\
\
The summand can be expanded (using the basic network equations 4) as:\
\
(6)\
\
$$\
\\frac {\\partial^ {2} E}{\\partial w \_ {i j} ^ {2}} = \\frac {\\partial^ {2} E}{\\partial a \_ {i} ^ {2}} x \_ {j} ^ {2}\
$$\
\
The second derivatives are back-propagated from layer to layer:\
\
$$\
\\frac {\\partial^ {2} E}{\\partial a \_ {i} ^ {2}} = f ^ {\\prime} \\left(a \_ {i}\\right) ^ {2} \\sum\_ {i} w \_ {l i} ^ {2} \\frac {\\partial^ {2} E}{\\partial a \_ {i} ^ {2}} - f ^ {\\prime \\prime} \\left(a \_ {i}\\right) \\frac {\\partial E}{\\partial x \_ {i}}\
$$\
\
We also need the boundary condition at the output layer, specifying the second derivative of E with respect to the last-layer weighted sums:\
\
(7)\
\
As can be seen, computing the diagonal Hessian is of the same order of complexity as computing the gradient. In some cases, the second term of the right hand side of the last two equations (involving the second derivative of f) can be neglected. This corresponds to the well-known Levenberg-Marquardt approximation, and has the interesting property of giving guaranteed positive estimates of the second derivative.\
\
$$\
f)\
$$\
\
* * *\
\
2.2 THE RECIPE\
\
The OBD procedure can be carried out as follows:\
\
1. Choose a reasonable network architecture\
\
2. Train the network until a reasonable solution is obtained\
\
3. Compute the second derivatives $ h\_{kk} $ for each parameter\
\
4. Compute the saliencies for each parameter: $ s\_{k}=h\_{k k} u\_{k}^{2}/2 $\
\
\
$$\
h \_ {k k}\
$$\
\
$$\
s \_ {k} = h \_ {k k} u \_ {k} ^ {2} / 2\
$$\
\
5. Sort the parameters by saliency and delete some low-saliency parameters\
\
6. Iterate to step 2\
\
\
Deleting a parameter is defined as setting it to 0 and freezing it there. Several variants of the procedure can be devised, such as decreasing the values of the low-saliency parameters instead of simply setting them to 0, or allowing the deleted parameters to adapt again after they have been set to 0.\
\
2.3 EXPERIMENTS\
\
The simulation results given in this section were obtained using back-propagation applied to handwritten digit recognition. The initial network was highly constrained and sparsely connected, having $ 10^{5} $ connections controlled by 2578 free parameters. It was trained on a database of segmented handwritten zipcode digits and printed digits containing approximately 9300 training examples and 3350 test examples. More details can be obtained from the companion paper (Le Cun et al., 1990b).\
\
$$\
1 0 ^ {5}\
$$\
\
Figure 1: (a) Objective function (in dB) v

[...truncated]