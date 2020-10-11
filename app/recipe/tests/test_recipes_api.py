from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

# Helper Functions


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }

    # Override any passed in param (ex: title='new Title')
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITest(TransactionTestCase):
    """Test unauth recipe api access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that auth is required"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TransactionTestCase):
    """Test auth recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@jmits.com',
            'password123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        """Test retrieving recipe"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Test retrieving recipe for user"""
        user2 = get_user_model().objects.create_user(
            'other@jmits.com',
            'password123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)

        res = self.client.get(url)

        # Only for single object
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test create recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPE_URL, payload)

        # retrieve the created recipe
        recipe = Recipe.objects.get(id=res.data['id'])

        # Validate every key-value pair
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag_1 = sample_tag(user=self.user, name='Vegan')
        tag_2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag_1.id, tag_2.id],
            'time_minutes': 60,
            'price': 20.00
        }
        res = self.client.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])

        # Get all tags associated with such recipe
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_1, tags)
        self.assertIn(tag_2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient_1 = sample_ingredient(user=self.user, name='Prawns')
        ingredient_2 = sample_ingredient(user=self.user, name='Ginger')
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient_1.id, ingredient_2.id],
            'time_minutes': 20,
            'price': 7.00
        }
        res = self.client.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)

    def test_partial_recipe_update(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {'title': 'Chicken tik', 'tags': [new_tag.id]}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spaghetti',
            'time_minutes': 25,
            'price': 5.00
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)