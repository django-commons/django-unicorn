# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/django-commons/django-unicorn/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                 |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| conftest.py                                                          |       21 |        2 |        4 |        2 |     84% |    83, 93 |
| example/apps/\_\_init\_\_.py                                         |        0 |        0 |        0 |        0 |    100% |           |
| example/apps/main/\_\_init\_\_.py                                    |        0 |        0 |        0 |        0 |    100% |           |
| example/books/\_\_init\_\_.py                                        |        1 |        0 |        0 |        0 |    100% |           |
| example/books/apps.py                                                |        3 |        0 |        0 |        0 |    100% |           |
| example/books/models.py                                              |        9 |        0 |        0 |        0 |    100% |           |
| example/coffee/\_\_init\_\_.py                                       |        1 |        0 |        0 |        0 |    100% |           |
| example/coffee/apps.py                                               |        3 |        0 |        0 |        0 |    100% |           |
| example/coffee/models.py                                             |       26 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/\_\_init\_\_.py                                  |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/cacher.py                                        |      101 |        1 |       40 |        1 |     99% |        58 |
| src/django\_unicorn/call\_method\_parser.py                          |       80 |        1 |       24 |        2 |     97% |31->49, 47 |
| src/django\_unicorn/components/\_\_init\_\_.py                       |        5 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/components/fields.py                             |        3 |        1 |        0 |        0 |     67% |         7 |
| src/django\_unicorn/components/mixins.py                             |        7 |        1 |        2 |        1 |     78% |        15 |
| src/django\_unicorn/components/unicorn\_template\_response.py        |      119 |       11 |       50 |        8 |     89% |75, 90, 94, 121-123, 141, 189, 198, 204, 211-212, 223->225, 247->250 |
| src/django\_unicorn/components/unicorn\_view.py                      |      527 |       32 |      234 |       22 |     92% |110->113, 213, 267-268, 300, 303->exit, 306, 309, 316->321, 318->317, 323->321, 347-348, 471->474, 482->485, 499-502, 530-531, 547->563, 572->571, 619-620, 650, 679-688, 693, 753->756, 776-777, 829->824, 832-834, 912, 1026-1027, 1128->1131, 1131->1139 |
| src/django\_unicorn/components/updaters.py                           |       18 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/decorators.py                                    |       25 |        0 |       10 |        1 |     97% |    35->38 |
| src/django\_unicorn/errors.py                                        |       26 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/management/commands/startunicorn.py              |      102 |        8 |       36 |        7 |     89% |40-41, 80, 99, 102, 117, 129, 173->177, 187 |
| src/django\_unicorn/serializer.py                                    |      212 |       15 |      116 |        8 |     92% |31-32, 59->63, 84, 144->140, 184-186, 222, 251-255, 282-288, 340->exit, 465->464 |
| src/django\_unicorn/settings.py                                      |       57 |        7 |       16 |        3 |     86% |25->28, 52-56, 59, 107-112 |
| src/django\_unicorn/signals.py                                       |       13 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/templatetags/\_\_init\_\_.py                     |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/templatetags/unicorn.py                          |      125 |        8 |       46 |        4 |     93% |24->27, 41, 48-49, 120, 127-130, 142->149, 179->182 |
| src/django\_unicorn/typer.py                                         |      192 |       38 |      102 |       12 |     78% |10-11, 22-25, 40-50, 107-111, 140->148, 155-157, 161->168, 190-191, 221->228, 238-244, 259-260, 269, 314-321, 325->331, 327->331, 332, 351->350 |
| src/django\_unicorn/typing.py                                        |        5 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/urls.py                                          |        4 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/utils.py                                         |       70 |        8 |       18 |        3 |     88% |74-78, 145->144, 148-151 |
| src/django\_unicorn/views/\_\_init\_\_.py                            |       43 |        3 |        2 |        0 |     93% |      9-12 |
| src/django\_unicorn/views/action.py                                  |       46 |        6 |        2 |        0 |     88% |22, 34, 47, 54, 61, 75 |
| src/django\_unicorn/views/action\_parsers/\_\_init\_\_.py            |        0 |        0 |        0 |        0 |    100% |           |
| src/django\_unicorn/views/action\_parsers/call\_method.py            |      142 |       14 |       70 |       12 |     87% |5-6, 27-32, 42, 51->54, 76, 90, 119, 200, 215->189, 228->189, 251, 257->exit, 263->257, 267 |
| src/django\_unicorn/views/action\_parsers/sync\_input.py             |       13 |        0 |        4 |        0 |    100% |           |
| src/django\_unicorn/views/action\_parsers/utils.py                   |       82 |        6 |       52 |        5 |     92% |93, 126, 129, 147-148, 153 |
| src/django\_unicorn/views/message.py                                 |      179 |       36 |       80 |       13 |     76% |63-64, 77, 91->99, 100-118, 143, 146, 149, 202-210, 231, 258, 264-266, 269-271, 281->255, 299-300, 306-307 |
| src/django\_unicorn/views/objects.py                                 |      101 |       55 |       40 |        0 |     41% |19-22, 25, 29-35, 44-90, 93, 105-116, 170-173 |
| src/django\_unicorn/views/request.py                                 |       68 |        4 |       34 |        5 |     91% |43, 47, 62->65, 65->68, 94, 97 |
| src/django\_unicorn/views/response.py                                |       90 |        6 |       36 |        7 |     90% |95, 144->197, 154, 165, 170, 180, 200 |
| src/django\_unicorn/views/utils.py                                   |       85 |        5 |       46 |        5 |     92% |18-19, 60->63, 74->exit, 91, 95-97, 143->148, 144->143 |
| tests/\_\_init\_\_.py                                                |        0 |        0 |        0 |        0 |    100% |           |
| tests/benchmarks/\_\_init\_\_.py                                     |        0 |        0 |        0 |        0 |    100% |           |
| tests/benchmarks/serializer/\_\_init\_\_.py                          |        0 |        0 |        0 |        0 |    100% |           |
| tests/benchmarks/serializer/test\_dumps.py                           |       53 |       19 |        0 |        0 |     64% |48-53, 57-79, 83-88, 92-118 |
| tests/call\_method\_parser/test\_parse\_args.py                      |       96 |        0 |        0 |        0 |    100% |           |
| tests/call\_method\_parser/test\_parse\_call\_method\_name.py        |       68 |        0 |        0 |        0 |    100% |           |
| tests/call\_method\_parser/test\_parse\_kwarg.py                     |       44 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_component.py                                  |      292 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_convert\_to\_dash\_case.py                    |        5 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_convert\_to\_pascal\_case.py                  |        5 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_convert\_to\_snake\_case.py                   |        5 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_create.py                                     |       13 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_get\_locations.py                             |       74 |        0 |        4 |        2 |     97% |15->19, 21->exit |
| tests/components/test\_is\_html\_well\_formed.py                     |       37 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_issue\_236.py                                 |       32 |        0 |        2 |        1 |     97% |  32->exit |
| tests/components/test\_issue\_650.py                                 |       27 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_issue\_668\_repro.py                          |       14 |        2 |        0 |        0 |     86% |     18-19 |
| tests/components/test\_mount\_redirect.py                            |       32 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_typer\_inheritance.py                         |       12 |        1 |        2 |        1 |     86% |        27 |
| tests/components/test\_unicorn\_template\_response.py                |       58 |        0 |        0 |        0 |    100% |           |
| tests/components/test\_unicorn\_template\_response\_recursion.py     |       30 |        0 |        2 |        1 |     97% |    54->57 |
| tests/integration/test\_basic.py                                     |      101 |       79 |        0 |        0 |     22% |26-28, 36-63, 67-86, 90-112, 120-142, 146-161, 165-187, 195-202, 210-217, 225-232, 240-247 |
| tests/management/\_\_init\_\_.py                                     |        0 |        0 |        0 |        0 |    100% |           |
| tests/management/commands/\_\_init\_\_.py                            |        0 |        0 |        0 |        0 |    100% |           |
| tests/management/commands/startunicorn/\_\_init\_\_.py               |        0 |        0 |        0 |        0 |    100% |           |
| tests/management/commands/startunicorn/test\_handle.py               |      130 |        0 |        0 |        0 |    100% |           |
| tests/serializer/test\_dumps.py                                      |      340 |        0 |        0 |        0 |    100% |           |
| tests/serializer/test\_exclude\_field\_attributes.py                 |       24 |        0 |        0 |        0 |    100% |           |
| tests/serializer/test\_model\_value.py                               |       32 |        0 |        0 |        0 |    100% |           |
| tests/templatetags/test\_unicorn.py                                  |       15 |        0 |        0 |        0 |    100% |           |
| tests/templatetags/test\_unicorn\_render.py                          |      280 |        0 |        8 |        4 |     99% |52->exit, 61->exit, 70->exit, 79->exit |
| tests/templatetags/test\_unicorn\_scripts.py                         |       30 |        0 |        0 |        0 |    100% |           |
| tests/test\_cacher.py                                                |      168 |        4 |       10 |        0 |     98% |134, 137, 255, 287 |
| tests/test\_model\_lifecycle.py                                      |       64 |        0 |        0 |        0 |    100% |           |
| tests/test\_settings.py                                              |       49 |        0 |        4 |        2 |     96% |69->72, 90->exit |
| tests/test\_signals.py                                               |      109 |        0 |        0 |        0 |    100% |           |
| tests/test\_typer.py                                                 |      129 |        2 |        0 |        0 |     98% |    14, 23 |
| tests/test\_utils.py                                                 |       60 |        2 |        0 |        0 |     97% |    52, 63 |
| tests/urls.py                                                        |        8 |        0 |        0 |        0 |    100% |           |
| tests/views/action\_parsers/\_\_init\_\_.py                          |        0 |        0 |        0 |        0 |    100% |           |
| tests/views/action\_parsers/call\_method/\_\_init\_\_.py             |        0 |        0 |        0 |        0 |    100% |           |
| tests/views/action\_parsers/call\_method/test\_call\_method\_name.py |      147 |        1 |        4 |        0 |     99% |        68 |
| tests/views/action\_parsers/test\_security.py                        |       77 |        0 |        0 |        0 |    100% |           |
| tests/views/action\_parsers/utils/\_\_init\_\_.py                    |        0 |        0 |        0 |        0 |    100% |           |
| tests/views/action\_parsers/utils/test\_set\_property\_value.py      |       86 |        0 |        0 |        0 |    100% |           |
| tests/views/fake\_components.py                                      |      131 |        5 |        4 |        2 |     95% |94, 121, 137, 174, 183 |
| tests/views/fake\_components\_with\_broken\_import.py                |        4 |        3 |        0 |        0 |     25% |       3-7 |
| tests/views/message/test\_call\_method.py                            |      181 |        0 |        2 |        0 |    100% |           |
| tests/views/message/test\_call\_method\_multiple.py                  |      170 |      136 |        6 |        0 |     19% |20-23, 32-41, 50-61, 66-90, 95-122, 127-154, 159-187, 197-231, 236-263, 268-295, 300-327, 333-360 |
| tests/views/message/test\_calls.py                                   |       91 |        0 |       12 |        3 |     97% |111->110, 160->159, 178->177 |
| tests/views/message/test\_child\_state\_propagation.py               |       65 |        1 |        8 |        1 |     97% |36->35, 40 |
| tests/views/message/test\_get\_property\_value.py                    |       18 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_hash.py                                    |      115 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_login\_required.py                         |       70 |        8 |        2 |        1 |     88% |41, 52, 102-103, 132-133, 150-151, 178->exit |
| tests/views/message/test\_message.py                                 |       80 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_nested\_method\_call.py                    |       25 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_set\_property.py                           |       39 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_sync\_input.py                             |       13 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_target.py                                  |       73 |        0 |        2 |        1 |     99% |    51->54 |
| tests/views/message/test\_toggle.py                                  |       20 |        0 |        0 |        0 |    100% |           |
| tests/views/message/test\_type\_hints.py                             |       48 |        0 |        0 |        0 |    100% |           |
| tests/views/message/utils.py                                         |       20 |        0 |        8 |        0 |    100% |           |
| tests/views/test\_fk\_loading.py                                     |       30 |        2 |        4 |        2 |     88% |    20, 68 |
| tests/views/test\_is\_component\_field\_model\_or\_unicorn\_field.py |       21 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_m2m\_overwriting.py                                |       28 |        1 |        4 |        2 |     91% |14, 18->exit |
| tests/views/test\_process\_component\_request.py                     |       24 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_security\_deep.py                                  |      323 |        6 |       20 |        1 |     98% |50, 53, 57, 73, 81, 84, 482->exit |
| tests/views/test\_unicorn\_dict.py                                   |       15 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_unicorn\_field.py                                  |       22 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_unicorn\_model.py                                  |       15 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_unicorn\_set\_property\_value.py                   |       38 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_unicorn\_view\_init.py                             |       36 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_unit\_views.py                                     |       66 |        0 |        0 |        0 |    100% |           |
| tests/views/test\_utils\_set\_property\_fk.py                        |       38 |        0 |        0 |        0 |    100% |           |
| tests/views/utils/\_\_init\_\_.py                                    |        0 |        0 |        0 |        0 |    100% |           |
| tests/views/utils/test\_construct\_model.py                          |       47 |       10 |        0 |        0 |     79% |     44-60 |
| tests/views/utils/test\_set\_property\_from\_data.py                 |      139 |        2 |        0 |        0 |     99% |     29-30 |
| **TOTAL**                                                            | **7355** |  **552** | **1172** |  **145** | **91%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/django-commons/django-unicorn/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/django-commons/django-unicorn/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/django-commons/django-unicorn/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/django-commons/django-unicorn/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fdjango-commons%2Fdjango-unicorn%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/django-commons/django-unicorn/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.