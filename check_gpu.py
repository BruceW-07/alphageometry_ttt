# import os
# import jax
# import tensorflow as tf

# def check_gpu_environment():
#     """检查并配置GPU环境"""
#     # 1. TensorFlow GPU检查
#     os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'  # 显示详细日志
#     physical_devices = tf.config.list_physical_devices('GPU')
    
#     # 2. JAX GPU检查
#     jax.config.update('jax_platform_name', 'gpu')
#     jax_devices = jax.devices()
    
#     # 3. CUDA环境检查
#     cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES')
    
#     return {
#         'tf_gpus': physical_devices,
#         'jax_devices': jax_devices,
#         'cuda_env': cuda_visible
#     }

# # 执行检查
# status = check_gpu_environment()
# print(f"环境状态:\n{status}")

import tensorflow as tf

print(tf.sysconfig.get_build_info())
# print("TensorFlow version: ", tf.__version__)
# print("GPU built with TensorFlow: ", tf.test.is_built_with_cuda())
# print("Can access GPU: ", tf.config.list_physical_devices('GPU'))