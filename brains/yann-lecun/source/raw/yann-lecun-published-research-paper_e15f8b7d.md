Gradient-Based Learning Applied to Document Recognition

Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner

Abstract—

Multilayer Neural Networks trained with the backpropagation algorithm constitute the best example of a successful Gradient-Based Learning technique. Given an appropriate network architecture, Gradient-Based Learning algorithms can be used to synthesize a complex decision surface that can classify high-dimensional patterns such as handwritten characters, with minimal preprocessing. This paper reviews various methods applied to handwritten character recognition and compares them on a standard handwritten digit recognition task. Convolutional Neural Networks, that are specifically designed to deal with the variability of 2D shapes, are shown to outperform all other techniques.

Real-life document recognition systems are composed of multiple modules including field extraction, segmentation, recognition, and language modeling. A new learning paradigm, called Graph Transformer Networks (GTN), allows such multi-module systems to be trained globally using Gradient-Based methods so as to minimize an overall performance measure.

A Graph Transformer Network for reading bank check is also described. It uses Convolutional Neural Network character recognizers combined with global training techniques to provides record accuracy on business and personal checks. It is deployed commercially and reads several million checks per day.

Keywords- Neural Networks, OCR, Document Recognition, Machine Learning, Gradient-Based Learning, Convolutional Neural Networks, Graph Transformer Networks, Finite State Transducers.

NOMENCLATURE

- GT Graph transformer.

- GTN Graph transformer network.

- TDNN Time delay neural network.

- SDNN Space displacement neural network.


I. INTRODUCTION

- HMM Hidden Markov model.

- NN Neural network.

- RBF Radial basis function.

- HOS Heuristic oversegmentation.


Over the last several years, machine learning techniques, particularly when applied to neural networks, have played an increasingly important role in the design of pattern recognition systems. In fact, it could be argued that the availability of learning techniques has been a crucial factor in the recent success of pattern recognition applications such as continuous speech recognition and handwriting recognition.

The main message of this paper is that better pattern recognition systems can be built by relying more on automatic learning, and less on hand-designed heuristics. This is made possible by recent progress in machine learning and computer technology. Using character recognition as a case study, we show that hand-crafted feature extraction can be advantageously replaced by carefully designed learning machines that operate directly on pixel images. Using document understanding as a case study, we show that the traditional way of building recognition systems by manually integrating individually designed modules can be replaced by a unified and well-principled design paradigm, called Graph Transformer Networks, that allows training all the modules to optimize a global performance criterion.

Since the early days of pattern recognition it has been known that the variability and richness of natural data, be it speech, glyphs, or other types of patterns, make it almost impossible to build an accurate recognition system entirely by hand. Consequently, most pattern recognition systems are built using a combination of automatic learning techniques and hand-crafted algorithms. The usual method of recognizing individual patterns consists in dividing the system into two main modules shown in figure 1. The first module, called the feature extractor, transforms the input patterns so that they can be represented by low-dimensional vectors or short strings of symbols that (a) can be easily matched or compared, and (b) are relatively invariant with respect to transformations and distortions of the input patterns that do not change their nature. The feature extractor contains most of the prior knowledge and is rather specific to the task. It is also the focus of most of the design effort, because it is often entirely hand-crafted. The classifier, on the other hand, is often general-purpose and trainable. One of the main problems with this approach is that the recognition accuracy is largely determined by the ability of the designer to come up with an appropriate set of features.

* * *

✁

merits of different feature sets for particular tasks.

Historically, the need for appropriate feature extractors was due to the fact that the learning techniques used by the classifiers were limited to low-dimensional spaces with easily separable classes \[1\]. A combination of three factors have changed this vision over the last decade. First, the availability of low-cost machines with fast arithmetic units allows to rely more on brute-force "numerical" methods than on algorithmic refinements. Second, the availability of large databases for problems with a large market and wide interest, such as handwriting recognition, has enabled designers to rely more on real data and less on hand-crafted feature extraction to build recognition systems. The third and very important factor is the availability of powerful machine learning techniques that can handle high-dimensional inputs and can generate intricate decision functions when fed with these large data sets. It can be argued that the recent progress in the accuracy of speech and handwriting recognition systems can be attributed in large part to an increased reliance on learning techniques and large training data sets. As evidence to this fact, a large proportion of modern commercial OCR systems use some form of multilayer Neural Network trained with back-propagation.

In this study, we consider the tasks of handwritten character recognition (Sections I and II) and compare the performance of several learning techniques on a benchmark data set for handwritten digit recognition (Section III). While more automatic learning is beneficial, no learning technique can succeed without a minimal amount of prior knowledge about the task. In the case of multi-layer neural networks, a good way to incorporate knowledge is to tailor its architecture to the task. Convolutional Neural Networks \[2\] introduced in Section II are an example of specialized neural network architectures which incorporate knowledge about the invariances of 2D shapes by using local connection patterns, and by imposing constraints on the weights. A comparison of several methods for isolated handwritten digit recognition is presented in section III. To go from the recognition of individual characters to the recognition of words and sentences in documents, the idea of combining multiple modules trained to reduce the overall error is introduced in Section IV. Recognizing variable-length objects such as handwritten words using multi-module systems is best done if the modules

manipulate directed graphs. This leads to the concept of trainable Graph Transformer Network (GTN) also introduced in Section IV. Section V describes the now classical method of heuristic over-segmentation for recognizing words or other character strings. Discriminative and non-discriminative gradient-based techniques for training a recognizer at the word level without requiring manual segmentation and labeling are presented in Section VI. Section VII presents the promising Space-Displacement Neural Network approach that eliminates the need for segmentation heuristics by scanning a recognizer at all possible locations on the input. In section VIII, it is shown that trainable Graph Transformer Networks can be formulated as multiple generalized transductions, based on a general graph composition algorithm. The connections between GTNs and Hidden Markov Models, commonly used in speech recognition is also treated. Section IX describes a globally trained GTN system for recognizing handwriting entered in a pen computer. This problem is known as "on-line" handwriting recognition, since the machine must produce immediate feedback as the user writes. The core of the system is a Convolutional Neural Network. The results clearly demonstrate the advantages of training a recognizer at the word

$$
Y ^ {p} = F \\left(Z ^ {p}, W\\right)
$$

There are several approaches to automatic machine learning, but one of the most successful approaches, popularized in recent years by the neural network community, can be called "numerical" or gradient-based learning. The learning machine computes a function $ Y^{p}=F(Z^{p},W) $ where $ Z^{p} $ is the p-th input pattern, and W represents the collection of adjustable parameters in the system. In a pattern recognition setting, the output $ Y^{p} $ may be interpreted as the recognized class label of pattern $ Z^{p} $ , or as scores or probabilities associated with each class. A loss function $ E^{p}=\\mathcal{D}(D^{p},F(W,Z^{p})) $ , measures the discrepancy between $ D^{p} $ , the "correct" or desired output for pattern $ Z^{p} $ , and the output produced by the system. The average loss function $ E\_{train}(W) $ is the average of the errors $ E^{p} $ over a set of labeled examples called the training set $ {(Z^{1},D^{1}),\\dots,(Z^{P},D^{P})} $

$$
E ^ {p} = \\mathcal {D} \\left(D ^ {p}, F \\left(W, Z ^ {p}\\right)\\right)
$$

$$
Z ^ {p}
$$

$$
E \_ {t r a i n} (W)
$$

$$
\\left{\\left(Z ^ {1}, D ^ {1}\\right), \\dots \\left(Z ^ {P}, D ^ {P}\\right) \\right}
$$

$$
D ^ {p}
$$

$$
E ^ {p}
$$

$$
Z ^ {p}
$$ that the gap between the expected error rate on the test set $ E\_{test} $ and the error rate on the training set $ E\_{train} $ decreases with the number of training samples approximately as $ E\_{test} - E\_{train} = k(h / P)^{\\alpha} $ (1)

$$
E \_ {t e s t}
$$

$$
E \_ {t r a i n}
$$

$$
E \_ {t e s t} - E \_ {t r a i n} = k \\left(h / P\\right) ^ {\\alpha}
$$

where P is the number of training samples, h is a measure of "effective capacity" or complexity of the machine \[6\], \[7\], $ \\alpha $ is a number between 0.5 and 1.0, and k is a constant. This gap always decreases when the number of training samples increases. Furthermore, as the capacity h increases, $ E\_{train} $ decreases. Therefore, when increasing the capacity h, there is a trade-off between the decrease of $ E\_{train} $ and the increase of the gap, with an optimal value of the capacity h that achieves the lowest generalization error $ E\_{test} $ . Most learning algorithms attempt to minimize $ E\_{train} $ as well as some estimate of the gap. A formal version of this is called structural risk minimization \[6\], \[7\], and is based on defining a sequence of learning machines of increasing capacity, corresponding to a sequence of subsets of the parameter space such that each subset is a superset of the previous subset. In practical terms, Structural Risk Minimization is implemented by minimizing $ E\_{train}+\\beta H(W) $ , where the function $ H(W) $ is called a regularization function, and $

$$
E \_ {t r}
$$

$$
h,
$$

$$
E \_ {t r a i n}
$$

$$
E \_ {t e s t}
$$

$$
E \_ {t r a i n}
$$

$$
E \_ {t r a i n} + \\beta H (W)
$$

$$
\\beta
$$

$$
W
$$

B. Gradient-Based Learning

$$
W \_ {k} = W \_ {k - 1} - \\epsilon \\frac {\\partial E (W)}{\\partial W}.
$$

The general problem of minimizing a function with respect to a set of parameters is at the root of many issues in computer science. Gradient-Based Learning draws on the fact that it is generally much easier to minimize a reasonably smooth, continuous function than a discrete (combinatorial) function. The loss function can be minimized by estimating the impact of small variations of the parameter values on the loss function. This is measured by the gradient of the loss function with respect to the parameters. Efficient learning algorithms can be devised when the gradient vector can be computed analytically (as opposed to numerically through perturbations). This is the basis o

[...truncated]