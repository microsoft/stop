# Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation

This is the repo for the paper: [Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation](https://arxiv.org/abs/2310.02304)

```
@article{zelikman2023self,
  title={Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation},
  author={Eric Zelikman, Eliana Lorch, Lester Mackey, Adam Tauman Kalai},
  journal={arXiv preprint arXiv:2310.02304},
  year={2023}
}
```

Abstract: Several recent advances in AI systems (e.g., Tree-of-Thoughts and Program-Aided Language Models) solve problems by providing a "scaffolding" program that structures multiple calls to language models to generate better outputs. A scaffolding program is written in a programming language such as Python. In this work, we use a language-model-infused scaffolding program to improve itself. We start with a seed "improver" that improves an input program according to a given utility function by querying a language model several times and returning the best solution. We then run this seed improver to improve itself. Across a small set of downstream tasks, the resulting improved improver generates programs with significantly better performance than its seed improver. Afterward, we analyze the variety of self-improvement strategies proposed by the language model, including beam search, genetic algorithms, and simulated annealing. Since the language models themselves are not altered, this is not full recursive self-improvement. Nonetheless, it demonstrates that a modern language model, GPT-4 in our proof-of-concept experiments, is capable of writing code that can call itself to improve itself. We critically consider concerns around the development of self-improving technologies and evaluate the frequency with which the generated code bypasses a sandbox.


# Legal Notices

Microsoft and any contributors grant you a license to any code in the repository under the [MIT License](https://opensource.org/licenses/MIT), see the
[LICENSE](LICENSE) file, and grant you a license to the Microsoft documentation and other data
in this repository under the [Creative Commons Attribution 4.0 International Public License](https://creativecommons.org/licenses/by/4.0/legalcode),
see the [DATA_LICENSE](data/DATA_LICENSE) file. 

Microsoft, Windows, Microsoft Azure and/or other Microsoft products and services referenced in the documentation
may be either trademarks or registered trademarks of Microsoft in the United States and/or other countries.
The licenses for this project do not grant you rights to use any Microsoft names, logos, or trademarks.
Microsoft's general trademark guidelines can be found at http://go.microsoft.com/fwlink/?LinkID=254653.

Privacy information can be found at https://privacy.microsoft.com/en-us/

Microsoft and any contributors reserve all other rights, whether under their respective copyrights, patents,
or trademarks, whether by implication, estoppel or otherwise.


