import unittest

import cat_vlog


class ComfyRegistrationTests(unittest.TestCase):
    def test_registers_every_node_used_by_importable_workflow(self):
        required = {
            "CatStoryPlanner", "CatShotFields", "CatReference", "CatImageGate",
            "CatSaveFrame", "CatVideoGate", "CatSaveClip", "CatFinish",
        }
        self.assertTrue(required <= set(cat_vlog.NODE_CLASS_MAPPINGS))
        self.assertTrue(all(hasattr(cat_vlog.NODE_CLASS_MAPPINGS[name], "INPUT_TYPES") for name in required))


if __name__ == "__main__":
    unittest.main()
